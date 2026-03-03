cwlVersion: v1.0

class: CommandLineTool
id: crop
requirements:
    InlineJavascriptRequirement: {}
    EnvVarRequirement:
      envDef:
        PYTHONPATH: /app
    ResourceRequirement:
      coresMax: 1
      ramMax: 512
hints:
  DockerRequirement:
    dockerPull: localhost/crop:latest
baseCommand: ["python", "-m", "app"]
arguments: []
inputs:
  item:
    type: string
    inputBinding:
        prefix: --input-item
  aoi:
    type: string
    inputBinding:
        prefix: --aoi
  epsg:
    type: string
    inputBinding:
        prefix: --epsg
  band:
    type: string
    inputBinding:
        prefix: --band
outputs:
  cropped:
    outputBinding:
        glob: '*.tif'
    type: File