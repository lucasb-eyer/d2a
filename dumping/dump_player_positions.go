package main

import (
    "bufio"
    "fmt"
    "log"
    "os"
    "strings"

    "compress/bzip2"
    "encoding/json"
    "github.com/dotabuff/manta"
)

// Using a struct here to marshal it into json so it auto-escapes.
type Demson struct {
    Tick uint32 `json:"tick"`
    //Name string `json:"name"`
    //Hero string `json:"hero"`
    //SteamId uint64 `json:"steamid"`
    PlayerId int32 `json:"player"`
    Pos [3]float32 `json:"pos"`
    C [3]uint64 `json:"pos_c"`
    V [3]float32 `json:"pos_v"`
    LifeState uint64 `json:"lifestate"`
    Life float32 `json:"hp"`
    Mana float32 `json:"mp"`
}


func getStrOrDie(e *manta.Entity, name string) string {
    v, found := e.GetString(name)
    if !found {
        log.Fatalf(fmt.Sprintf("Didn't find %s!", name))
    }
    return v
}


func getI32OrDie(e *manta.Entity, name string) int32 {
    v, found := e.GetInt32(name)
    if !found {
        log.Fatalf(fmt.Sprintf("Didn't find %s!", name))
    }
    return v
}


func getF32OrDie(e *manta.Entity, name string) float32 {
    v, found := e.GetFloat32(name)
    if !found {
        log.Fatalf(fmt.Sprintf("Didn't find %s!", name))
    }
    return v
}


func getU32OrDie(e *manta.Entity, name string) uint32 {
    v, found := e.GetUint32(name)
    if !found {
        log.Fatalf(fmt.Sprintf("Didn't find %s!", name))
    }
    return v
}


func getU64OrDie(e *manta.Entity, name string) uint64 {
    v, found := e.GetUint64(name)
    if !found {
        log.Fatalf(fmt.Sprintf("Didn't find %s!", name))
    }
    return v
}


func coord(c [3]uint64, v [3]float32) (x, y, z float32) {
    const MAX_COORD = 16384
    const cellwidth = 1 << 7;  // Saw somewhere else this should be 1 << 8, but data don't agree, yo!
    // TODO: Where this at, yo?
    // cellwidth = 1 << entity[(u'DT_BaseEntity', u'm_cellbits')]

    x = float32(c[0]*cellwidth - MAX_COORD) + v[0]
    y = float32(c[1]*cellwidth - MAX_COORD) + v[1]
    z = float32(c[2]*cellwidth - MAX_COORD) + v[2]
    return
}


func main() {
    // Create a new parser instance from a file. Alternatively see NewParser([]byte)
    f, err := os.Open(os.Args[1])
    if err != nil {
        log.Fatalf("unable to open file: %s", err)
    }
    defer f.Close()

    // create a reader
    br := bufio.NewReader(f)
    // create a bzip2.reader, using the reader we just created
    cr := bzip2.NewReader(br)

    p, err := manta.NewStreamParser(cr)
    if err != nil {
        log.Fatalf("unable to create parser: %s", err)
    }

    player_names := make([]string, 10)
    player_steam := make([]uint64, 10)
    player_heros := make([]string, 10)

    // Extract player names and steam IDs.
    p.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
        if e.GetClassName() != "CDOTA_PlayerResource" {
            return nil
        }

        // Don't know how to get array length anymore, see
        // https://github.com/dotabuff/manta/issues/108
        // So just assume that the players are always the first 10 in the vector
        // which also contains casters and camera crew.
        for iplayer := 0 ; iplayer < 10 ; iplayer++ {
            prefix := fmt.Sprintf("m_vecPlayerData.%04d", iplayer)
            player_names[iplayer] = getStrOrDie(e, prefix + ".m_iszPlayerName")
            player_steam[iplayer] = getU64OrDie(e, prefix + ".m_iPlayerSteamID")
        }

        // TODO: Since these are immutable, could detach once we've got 'em all?
        //       maybe only use created op.
        return nil
    })

    // Extract player positions.
    p.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
        // Only care about changes for now, no creating/removing to avoid duplicates per tick.
        if op != manta.EntityOpUpdated {
            return nil
        }

        // We only care about heroes.
        if !strings.HasPrefix(e.GetClassName(), "CDOTA_Unit_Hero_") {
            return nil
        }

        // Skip illus for now.
        const HANDLE_NONE = 16777215
        if repl, found := e.GetUint32("m_hReplicatingOtherHeroModel") ; found && repl != HANDLE_NONE {
            return nil
        }

        demson := &Demson{
            Tick: p.Tick,
            // The following are just defaults and get changed, if available.
            //Hero: e.ClassName[len("CDOTA_Unit_Hero_"):],
            PlayerId: -1,
            LifeState: ^uint64(0),
            Life: -1,
            Mana: -1,
        }

        // Fill in the position
        demson.C[0] = getU64OrDie(e, "CBodyComponent.m_cellX")
        demson.C[1] = getU64OrDie(e, "CBodyComponent.m_cellY")
        demson.C[2] = getU64OrDie(e, "CBodyComponent.m_cellZ")
        demson.V[0] = getF32OrDie(e, "CBodyComponent.m_vecX")
        demson.V[1] = getF32OrDie(e, "CBodyComponent.m_vecY")
        demson.V[2] = getF32OrDie(e, "CBodyComponent.m_vecZ")
        demson.Pos[0], demson.Pos[1], demson.Pos[2] = coord(demson.C, demson.V)

        // Fill in the player's name and steam ID
        demson.PlayerId = getI32OrDie(e, "m_iPlayerID")
        //demson.Name, demson.SteamId = player_names[iplayer], player_steam[iplayer]

        // Fill in the hero's name (ID, not nicely readable)
        if player_heros[demson.PlayerId] == "" {
            if idx, found := e.GetInt32("m_pEntity.m_nameStringableIndex") ; found {
                if hero, found := p.LookupStringByIndex("EntityNames", idx) ; found {
                    player_heros[demson.PlayerId] = hero
                }
            }
        }

        // Fill in the lifestate,
        // see https://github.com/ValveSoftware/source-sdk-2013/blob/master/mp/src/public/const.h#L274-L278
        // Example occurence histogram:
        //  547722   m_lifeState: %!s(uint64=0)   // LIFE_ALIVE
        //    2526   m_lifeState: %!s(uint64=1)   // LIFE_DYING
        //    3507   m_lifeState: %!s(uint64=2)   // LIFE_DEAD
        demson.LifeState = getU64OrDie(e, "m_lifeState")

        // HP and MP as percentage
        demson.Life = float32(getI32OrDie(e, "m_iHealth")) / float32(getI32OrDie(e, "m_iMaxHealth"))
        demson.Mana = getF32OrDie(e, "m_flMana") / getF32OrDie(e, "m_flMaxMana")

        // Format and output as json
        if data, err := json.Marshal(demson) ; err == nil {
            fmt.Println(string(data))
        } else {
            return err
        }

        // Get world-coordinates.
        // Adding 256 per cell because the max of v is [255.968750 255.968750 255.968750]
        // cx [66,190], cy [68,190], cz [128,140]
        //log.Printf("[%f, %f, %f]", float32(cx)*256.0+vx, float32(cy)*256.0+vy, float32(cz)*256.0+vz)

        // Also: https://www.reddit.com/r/DotA2/comments/1805d9/the_complete_dota2_map_25_megapixel_resolution/c8axm02/
        //
        // New map: https://www.reddit.com/r/DotA2/comments/4xfegu/the_687_dota2_map_higher_resolution_version_in/

        // TODO: Where this from?
        // m_iUnitNameIndex == 15
        return nil
    })

    // Start parsing the replay!
    if err := p.Start() ; err != nil {
        os.Exit(1)
    }

    if data, err := json.Marshal(player_names) ; err == nil {
        os.Stderr.WriteString(string(data))
        os.Stderr.WriteString("\n")
    } else {
        log.Fatalf("Error: %s", err)
    }

    if data, err := json.Marshal(player_steam) ; err == nil {
        os.Stderr.WriteString(string(data))
        os.Stderr.WriteString("\n")
    } else {
        log.Fatalf("Error: %s", err)
    }

    if data, err := json.Marshal(player_heros) ; err == nil {
        os.Stderr.WriteString(string(data))
        os.Stderr.WriteString("\n")
    } else {
        log.Fatalf("Error: %s", err)
    }
}
