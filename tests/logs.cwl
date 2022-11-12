$graph:
- class: Workflow
  id: main

  requirements:
  - class: MultipleInputFeatureRequirement
  - class: ScatterFeatureRequirement

  inputs:
    message:
      type: string[]
  outputs:
    wf_outputs:
      outputSource:
        - step_one/results
      type: string[]
  steps:
    step_one:
      in:
        message: message
      out:
      - results
      run: '#clt'
      scatter: message
      scatterMethod: dotproduct

- class: CommandLineTool
  id: clt
  baseCommand: ['/bin/sh', 'run.sh']

  stdout: output.txt

  inputs:
    message:
      type: string
      inputBinding: {}
  outputs:
    results:
      type: string
      outputBinding:
        glob: output.txt
        loadContents: true
        outputEval: $(self[0].contents)
  hints:
    DockerRequirement:
      dockerPull: docker.io/python:3.11.0-buster

  requirements:
    InlineJavascriptRequirement: {}
    EnvVarRequirement:
      envDef:
        PYTHONPATH: $HOME
        PROJ_LIB: /srv/conda/envs/notebook/share/proj
    InitialWorkDirRequirement:
      listing:
        - entryname: run.sh
          entry: |-
            python -m app $@
        - entryname: app.py
          entry: |-
            import sys
            from time import sleep
            print("log entry $(inputs.message)", file=sys.stderr)
            sleep(3)
            print("log entry 2", file=sys.stderr)
            sleep(3)
            print("log entry 3", file=sys.stderr)
            sleep(3)
            print("out $(inputs.message)")

$namespaces:
  s: https://schema.org/
cwlVersion: v1.0
schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf
s:softwareVersion: 0.3.2
