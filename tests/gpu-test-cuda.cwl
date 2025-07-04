cwlVersion: v1.2
class: CommandLineTool
id: main

inputs:
  reference:
    type: string

outputs: []
  # test_output:
  #   type: File
  #   outputBinding:
  #     glob: test-result.txt

baseCommand: ["python", "gpu_test.py"]

arguments:
  - $(inputs.reference)

requirements:
  
  DockerRequirement:
    dockerPull: pytorch/pytorch:2.7.1-cuda11.8-cudnn9-runtime

  ResourceRequirement:
    coresMin: 2
    ramMin: 1000
    ramMax: 2000

  InitialWorkDirRequirement:
    listing:
      - entryname: gpu_test.py
        entry: |
          import torch
          import torch.nn as nn
          import torch.optim as optim

          # Check if GPU is available
          device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
          print(f"Using device: {device}")

          # Dummy dataset
          x = torch.randn(100, 10).to(device)
          y = torch.randn(100, 1).to(device)

          # Simple model
          model = nn.Sequential(
              nn.Linear(10, 50),
              nn.ReLU(),
              nn.Linear(50, 1)
          ).to(device)  # Move model to GPU if available

          # Loss and optimizer
          criterion = nn.MSELoss()
          optimizer = optim.Adam(model.parameters(), lr=0.001)

          # Training loop
          for epoch in range(10):
              model.train()
              
              outputs = model(x)
              loss = criterion(outputs, y)

              optimizer.zero_grad()
              loss.backward()
              optimizer.step()

              print(f"Epoch [{epoch+1}/10], Loss: {loss.item():.4f}")

          # with open("test-result.txt", "w") as f:
          #     f.write("Test run complete.\n")
          #     f.write(f"{device} is Available\n")


$namespaces:
  cwltool: "http://commonwl.org/cwltool#"
