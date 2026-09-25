# Lab 3 - Docker

## Question 1

My model was registered as version 1.

The logged model artifact belongs to a specific MLflow run and is one of the outputs produced by that run. A registered model is added to the Model Registry with a name and version, which makes it easier to manage and use later.

## Question 2

MLflow now uses aliases instead of the old stages. In my case, I assigned the alias `champion` to version 1 of the `food11` model.

The model version is separate from the run because the run contains the whole experiment information, while the model version is used to manage the trained model itself. An alias is useful because I can move `champion` to another version later without changing my serving code.

## Question 3

I used the MLflow URI `models:/food11@champion` instead of loading a `.pth` file directly. This lets the API load the model that is registered as `champion` without depending on a specific model file path.

If I train a better model later, I can register the new version and move the `champion` alias to it. I would not need to change the model URI in `serve.py`.

## Question 4

I copied `pyproject.toml` and `uv.lock` before the source code so Docker can cache the dependency installation separately.

If I only change something in `serve.py`, the dependencies did not change, so Docker can reuse the cached dependency layer instead of installing all the packages again.

## Question 6

Without `.dockerignore`, Docker would also send files that are not needed for the image, such as the dataset, `.venv`, MLflow files, and `.git`. This makes the build context bigger and can make the build slower.

In my Dockerfile, these folders are not copied into the final image because I only copy the files I need, so sending them would not directly break the build. However, `.venv` should still be excluded because it was created on Windows while the container uses Linux. The other folders like `data`, `mlruns`, and `.git` are also not needed for the API.