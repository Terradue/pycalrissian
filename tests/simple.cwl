cwlVersion: v1.0
class: CommandLineTool
requirements:
  DockerRequirement:
    dockerPull: docker.io/bash:4.4
  ResourceRequirement:
    coresMax: 2
    ramMax: 256
baseCommand: echo
inputs:
  message:
    type: string
    inputBinding:
      position: 1
outputs: []
