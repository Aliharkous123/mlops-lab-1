# Lab 4 - Orchestrating the app with Docker Compose

## Question 1

If I don't mount a volume to `/mlflow-data`, the MLflow data stays inside the container. If I stop and remove that container and create a new one from the same image, the old data is gone and the MLflow UI starts empty again.

## Question 2

I used a named volume because I want the MLflow database and artifacts to stay even if the container is removed or recreated. Docker manages the volume for me and it is not stored directly in my project folder. A bind mount would also work, but it would use a specific folder from my machine instead.

## Question 3

In this lab, Docker Compose puts the services on the same network and lets them find each other using their service names. This is why the inference container can use `http://mlflow:5000`. In Lab 3, MLflow was running on my Windows host, so I had to use `host.docker.internal` instead.

## Question 4

I used the `INFERENCE_URL` environment variable so the frontend is not tied to one address. With Compose I can set it to `http://inference:8000`, but if I run the frontend by itself later, I can give it another address without changing the code.

## Question 5

The inference service doesn't need a published port because I don't access it directly from my computer. The frontend and inference containers are on the same Compose network, so the frontend can reach it using `http://inference:8000`. Only MLflow and the frontend need ports published to the host.

## Question 6

`depends_on` starts the MLflow container before the inference container, but it doesn't mean that MLflow is already ready to receive requests. If inference tries to load the model too early, the connection can fail and the inference container can exit. I can see the error using `docker compose logs inference`.

## Question 7

When I ran `docker compose ps`, MLflow had port `5000` published and the frontend had port `8501` published. The inference service only showed `8000/tcp`, so its port was not published to my host. This is what I expected from my `docker-compose.yml` because inference is only used internally by the frontend.

## Question 8

Changing the model version does not change the model already loaded by the running inference service because `serve.py` loads it only when the service starts. In my setup, I created version 2 and changed the `champion` alias to point to it instead of using Staging. To make inference load the new version, I used:

`docker compose restart inference`

I didn't need to rebuild the image. Since versions 1 and 2 came from the same run in my test, the prediction stayed the same.

## Question 9

Restarting is enough because the inference image already contains the application code and its dependencies, while the model is loaded from MLflow when the container starts. So after changing the model version used by the service, restarting inference makes it load the selected version again without rebuilding the image.

## Question 10

After `docker compose down` and then `docker compose up`, my MLflow data was still there because the `mlflow-data` named volume was not deleted.

When I used `docker compose down -v`, the volume was deleted too. After starting the stack again, MLflow was empty and my previous experiment, registered model, versions and alias were gone. This showed me that the volume keeps the MLflow data even when the containers are removed, unless I also delete the volume.

## Question 11

Docker Compose works well for running these services together on one machine, but it doesn't give me full orchestration across several machines. If I wanted three inference replicas behind a load balancer or wanted MLflow to keep working if one machine failed, I would need something like Kubernetes. It can manage replicas, load balancing, recovery and services across multiple machines. MLflow would also need storage and a database that are not dependent on only one machine.