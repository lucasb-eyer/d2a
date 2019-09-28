package main

import (
    "bufio"
    "log"
    "os"

    "compress/bzip2"
    "github.com/dotabuff/manta"
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

    p.Callbacks.OnAny(func(m interface{}) error {
        log.Printf("%s", m)
        return nil
    })

    // Start parsing the replay!
    p.Start()
}
