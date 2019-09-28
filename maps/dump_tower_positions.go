package main

import (
    "bufio"
    "fmt"
    "log"
    "os"

    "compress/bzip2"
    "github.com/dotabuff/manta"
)


func getF32OrDie(e *manta.Entity, name string) (v float32) {
    v, found := e.GetFloat32(name)
    if !found {
        log.Fatalf(fmt.Sprintf("Didn't find %s!", name))
    }
    return
}


func getU64OrDie(e *manta.Entity, name string) (v uint64) {
    v, found := e.GetUint64(name)
    if !found {
        log.Fatalf(fmt.Sprintf("Didn't find %s!", name))
    }
    return
}


func coord(cx, cy, cz uint64, vx, vy, vz float32) (x, y, z float32) {
    const MAX_COORD = 16384
    const cellwidth = 1 << 8;
    // TODO: Where this at, yo?
    // cellwidth = 1 << entity[(u'DT_BaseEntity', u'm_cellbits')]

    x = float32(cx*cellwidth - MAX_COORD) + vx
    y = float32(cy*cellwidth - MAX_COORD) + vy
    z = float32(cz*cellwidth - MAX_COORD) + vz
    return
}


func entity_coord(e *manta.Entity) (cx, cy, cz uint64, vx, vy, vz float32, x, y, z float32) {
    cx = getU64OrDie(e, "CBodyComponent.m_cellX")
    cy = getU64OrDie(e, "CBodyComponent.m_cellY")
    cz = getU64OrDie(e, "CBodyComponent.m_cellZ")
    vx = getF32OrDie(e, "CBodyComponent.m_vecX")
    vy = getF32OrDie(e, "CBodyComponent.m_vecY")
    vz = getF32OrDie(e, "CBodyComponent.m_vecZ")
    x, y, z = coord(cx, cy, cz, vx, vy, vz)
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

    // Extract player positions.
    p.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
        // Only care about when they are created (they don't move!)
        if op & manta.EntityOpCreated == 0 {
            return nil
        }

        // We only care about towers.
        if e.GetClassName() != "CDOTA_BaseNPC_Tower" {
            return nil
        }

        cx, cy, cz, vx, vy, vz, x, y, z:= entity_coord(e)
        fmt.Printf("%d %d %d %f %f %f %f %f %f\n", cx, cy, cz, vx, vy, vz, x, y, z)

        // Why golang can't be reasonable and allow this one FFS!?
        // fmt.Printf("%d %d %d %f %f %f %f %f %f\n", entity_coord(e)...)

        return nil
    })

    // Start parsing the replay!
    if err := p.Start() ; err != nil {
        os.Exit(1)
    }
}
