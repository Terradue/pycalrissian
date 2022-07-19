class: CommandLineTool
cwlVersion: v1.0
requirements:
  DockerRequirement:
    dockerPull: docker.io/bash:4.4
  ResourceRequirement:
    coresMax: 2
    ramMax: 256
inputs: []
outputs:
  cow:
    type: File
    outputBinding:
      glob: cow
baseCommand: ["-c", "echo $A && echo 'moo' > cow && echo $A >> cow cat cow && sleep 500"]
