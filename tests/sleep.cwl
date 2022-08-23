cwlVersion: v1.0
class: CommandLineTool
requirements:
  DockerRequirement:
    dockerPull: docker.io/bash:4.4
  ResourceRequirement:
    coresMax: 1
    ramMax: 256
  InitialWorkDirRequirement:
      listing:
        - entryname: run.sh
          entry: |-
            sleep 120
            echo $1
baseCommand: ["/bin/sh", "run.sh"]
inputs:
  message:
    type: string
    inputBinding:
      position: 1
outputs: []
