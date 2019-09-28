package main

import (
    "bufio"
    "fmt"
    "log"
    "os"
    "sort"
    "strings"

    "compress/bzip2"
    "github.com/dotabuff/manta"
    "github.com/dotabuff/manta/dota"
)


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

    p.OnEntity(func(e *manta.Entity, op manta.EntityOp) error {
        // Filter by prefix if any is specified.
        // CDOTA_BaseNPC_Tower, CDOTA_BaseNPC_Barracks, ...
        if len(os.Args) == 3 && !strings.HasPrefix(e.GetClassName(), os.Args[2]) {
            return nil
        }

        if len(os.Args) == 2 {
            // In case we do unfiltered printing of all entities, don't print properties (e.Map())
            // because that's way too much - GB upon GB per replay.
            fmt.Printf("class:%s (cid:%d, idx:%d, ser:%d)\n", e.GetClassName(), e.GetClassId(), e.GetIndex(), e.GetSerial())
            // fmt.Printf("class:%s (cid:%d, idx:%d, ser:%d): %s\n", e.GetClassName(), e.GetClassId(), e.GetIndex(), e.GetSerial(), e.Map())
        } else {
            fmt.Printf("class:%s (cid:%d, idx:%d, ser:%d): %s\n", e.GetClassName(), e.GetClassId(), e.GetIndex(), e.GetSerial(), op)

            // TODO: Ideally we would only print the changed ones, but eh...
            properties := e.Map()
            for _, k := range sortedkeys(properties) {
                fmt.Printf("  %s: %s\n", k, properties[k])
            }
        }
        return nil
    })

    p.Callbacks.OnCDOTAMatchMetadataFile(func(m *dota.CDOTAMatchMetadataFile) error {
        fmt.Printf("META: %s\n", m)
        return nil
    })

    // Start parsing the replay!
    p.Start()
}


func sortedkeys(m map[string]interface{}) []string {
    keys := make([]string, len(m))

    i := 0
    for k := range m {
        keys[i] = k
        i++
    }

    sort.Strings(keys)

    return keys
}
