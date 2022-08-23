cwlVersion: v1.0
class: CommandLineTool
requirements:
  DockerRequirement:
    dockerPull: docker.io/bash:4.4
  ResourceRequirement:
    coresMax: 128
    ramMax: 2560000
baseCommand: echo
inputs:
  message:
    type: string
    inputBinding:
      position: 1
outputs: []
