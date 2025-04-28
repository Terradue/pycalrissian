cwlVersion: v1.0

class: CommandLineTool
id: main
inputs:
  reference:
    type: string
outputs:
  staged:
    type: Directory
    outputBinding:
      glob: .
baseCommand: 
- python
- stage.py
arguments:
- $( inputs.reference )
requirements:
  DockerRequirement:
    dockerPull: ghcr.io/terradue/app-package-training-bids23/stage:1.0.0
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - entryname: stage.py
        entry: |-
          import pystac
          import stac_asset
          import asyncio
          import os
          import sys

          config = stac_asset.Config(warn=True)

          async def main(href: str):
              print("HREF: ",href)
              item = pystac.read_file(href)
              cwd = os.getcwd()
              
              
              
              cat = pystac.Catalog(
                  id="catalog",
                  description=f"catalog with staged {item.id}",
                  title=f"catalog with staged {item.id}",
              )
              cat.add_item(item)
              print(cat.describe())
              

              return cat

          href = sys.argv[1]

          asyncio.run(main(href))