package main

import (
    "bufio"
    "fmt"
    "log"
    "os"
    "strings"

    "compress/bzip2"
    "github.com/dotabuff/manta"
)


func getF32OrDie(e *manta.Entity, name string) float32 {
    v, found := e.GetFloat32(name)
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


// Convert cell-vector coordinates into [-1,1] world coordinates.
func coord(c [3]uint64, v [3]float32) (x, y, z float32) {
    x = (float32(c[0]*128) + v[0]) / 8192. - 2.0
    y = 2.0 - (float32(c[1]*128) + v[1]) / 8192.
    z = (float32(c[2]*128) + v[2]) / 8192. - 2.0
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

    // We want to avoid repeats at the same spot. So need some bookkeeping.
    last_lifestates := make(map[string]uint64)

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

        // Skip illus too.
        const HANDLE_NONE = 16777215
        if repl, found := e.GetUint32("m_hReplicatingOtherHeroModel") ; found && repl != HANDLE_NONE {
            return nil
        }

        // Only print a death location if the life state switched from alive to dying.
        // It is the most reliable way I found.
        // 0: alive, 1: dying, 2: death.
        // See https://github.com/ValveSoftware/source-sdk-2013/blob/0d8dceea4310fde5706b3ce1c70609d72a38efdf/mp/src/public/const.h#L274
        lifestate := getU64OrDie(e, "m_lifeState")
        reincarnating, _ := e.GetBool("m_bReincarnating")  // Aegis, WK Ult, ...
        summoned, _ := e.GetBool("m_bIsSummoned")  // BeastMaster boar/hawk for example.
        if lifestate == 1 && last_lifestates[e.GetClassName()] == 0 && !reincarnating && !summoned {
            // Fill in the position
            c := [...]uint64{
                getU64OrDie(e, "CBodyComponent.m_cellX"),
                getU64OrDie(e, "CBodyComponent.m_cellY"),
                getU64OrDie(e, "CBodyComponent.m_cellZ")}
            v := [...]float32{
                getF32OrDie(e, "CBodyComponent.m_vecX"),
                getF32OrDie(e, "CBodyComponent.m_vecY"),
                getF32OrDie(e, "CBodyComponent.m_vecZ")}

            // Send one team to stdout, the other to stderr.
            out := os.Stdout
            if getU64OrDie(e, "m_iTeamNum") == 3 {  // values are 2 or 3
                out = os.Stderr
            }

            // x, y, _ := coord(c, v)
            // fmt.Fprintf(out, "%s %d %f %f\n", e.GetClassName(), lifestate, x, y)
            fmt.Fprintf(out, "%d %d %f %f\n", c[0], c[1], v[0], v[1])
        }
        last_lifestates[e.GetClassName()] = lifestate
        return nil
    })

    // Start parsing the replay!
    if err := p.Start() ; err != nil {
        os.Exit(1)
    }
}
