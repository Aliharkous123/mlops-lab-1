### Question 1
My model was registered as version 1. The logged model artifact belongs to one specific training run, while the registered model gives me a model name and a version that I can manage and reuse more easily.

### Question 2
MLflow now uses aliases like `champion` and `challenger` instead of the old `Staging` and `Production` stages. Having different model versions makes it easier to keep and manage the models I trained. The alias is useful because if I get a better model later, I can move `champion` to the new version without changing my serving code.

### Question 3
I loaded the model using `models:/food11@champion` because this lets MLflow handle which model version should be used. If I loaded a `.pth` file directly, I would have to manage the file path myself. With the alias, if I get a better model later, I only need to assign `champion` to the new version and the serving code can stay the same.

### Question 4
I copied `pyproject.toml` and `uv.lock` first so Docker can install the dependencies in a separate cached layer. This is useful because the dependencies do not change every time I modify my code. For example, if I only change something in `serve.py`, Docker can reuse the dependency layer instead of installing everything again.

### Question 5
From `docker history`, I noticed that the biggest part of my image is the virtual environment, which is around 1.43 GB. The source code itself is only around 49.2 kB. I used a multi-stage build so build-related things do not have to stay in the final image. I did not create a separate single-stage image, so I do not have an exact size comparison between the two.

### Question 6
If I forget .dockerignore, Docker sends unnecessary files like data, .venv, mlruns and .git as part of the build context, which makes it larger and can slow down the build. Sending them to the Docker daemon does not necessarily break the build by itself, but copying my local .venv into the image could cause problems because it was created on Windows while the container runs Linux.

### Question 7
I could not use `127.0.0.1:5000` from inside the container because localhost there refers to the container itself. My MLflow server was running on my Windows machine, so I used `host.docker.internal` to let the container reach the host machine.

### Question 8
I stopped the container and started a new one using the same `food11-api:latest` image without rebuilding it. The API worked again and both `/health` and `/predict` returned successful responses. This showed me that I do not need to rebuild the image every time I start a container. The application and its dependencies are in the image, while the model is loaded through MLflow at runtime. In my setup I also mounted `mlruns` so the container could access the local model artifacts.

### Question 9
The Dockerfile is already saved in Git, but the Docker image is still only on my computer. If I want another machine or a CI/Kubernetes environment to use the same image, I need to push it to a container registry such as Docker Hub or GitHub Container Registry. I should also use a specific tag or digest to make sure the same image is used. Since my model is loaded from MLflow at runtime, the other machine also needs to be able to access the MLflow server and the model artifacts.