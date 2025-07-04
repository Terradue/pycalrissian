cwlVersion: v1.2
class: CommandLineTool
id: main

inputs:
  reference:
    type: string

outputs:
  test_output:
    type: File
    outputBinding:
      glob: test-result.txt

baseCommand: ["python", "gpu_test.py"]

arguments:
  - $(inputs.reference)

requirements:
  EnvVarRequirement:
    envDef:
      LD_LIBRARY_PATH: /usr/local/nvidia/lib:/usr/local/nvidia/lib64
      PATH: /usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  
  DockerRequirement:
    dockerPull: nvcr.io/nvidia/tensorflow:23.12-tf2-py3

  ResourceRequirement:
    coresMin: 2
    ramMin: 1000
    ramMax: 2000

  InitialWorkDirRequirement:
    listing:
      - entryname: gpu_test.py
        entry: |
          import tensorflow as tf
          import sys 
          from tensorflow.keras import layers, models
          import os
          print("🔍 Checking GPU availability...")
          gpus = tf.config.list_physical_devices('GPU')
          if gpus:
              print("✅ GPU is available")
          else:
              print("❌ GPU is NOT available")

          # Minimal test on MNIST
          (x_train, y_train), _ = tf.keras.datasets.mnist.load_data()
          x_train, y_train = x_train[:10] / 255.0, y_train[:10]
          x_train = x_train[..., tf.newaxis]

          model = models.Sequential([
              layers.Input(shape=(28, 28, 1)),
              layers.Flatten(),
              layers.Dense(32, activation='relu'),
              layers.Dense(10, activation='softmax')
          ])
          model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
          model.fit(x_train, y_train, epochs=3, batch_size=2)

          with open("test-result.txt", "w") as f:
              f.write("Test run complete.\n")
              f.write(f"GPU Available: {bool(gpus)}\n")

$namespaces:
  cwltool: "http://commonwl.org/cwltool#"
