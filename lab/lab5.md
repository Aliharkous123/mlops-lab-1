\# Lab 5 – CI/CD for Food11



\## 1. Introduction



In this lab, I worked on the CI/CD part of my Food11 project. The goal was to automate the tests using GitHub Actions instead of checking everything manually each time.



I also worked on data validation, Docker testing and model promotion with MLflow.



\## 2. Code Changes and Testing



I started by modifying `data.py`. I separated some parts of the preprocessing code into functions so I could test them without running the whole script.



I also changed `serve.py` to make it possible to start the API without loading the trained model. I used `SKIP\_MODEL=1` for that.



After these changes, I wrote tests for the data functions and the API.



I ran:



`uv run --no-sync python -m pytest -q`



The result was \*\*5 passed, 4 warnings\*\*. The warnings were related to deprecated functions, but they did not cause the tests to fail.



I also ran Ruff to check the code:



`uv run --no-sync ruff check src tests`



Ruff found an import-order problem in `promote.py`. I fixed it using `ruff check src tests --fix`, then ran the check again.



This time I got `All checks passed!`.



\## 3. Data Validation



I wrote `validate\_data.py` to check the Food11 dataset before training.



The script checks if all 11 classes are present in each split, if the images are RGB with size 128×128, and if each class has enough images. It also checks for duplicate images and compares the class distribution between training and validation.



I ran the script on the mini dataset with a minimum of 20 images per class.



Four checks passed, but one failed because I had duplicate images between the validation and evaluation folders.



The duplicate pairs were:



\- `evaluation/Seafood/8\_100.jpg` and `validation/Seafood/8\_102.jpg`

\- `evaluation/Seafood/8\_108.jpg` and `validation/Seafood/8\_110.jpg`



I did not expect this problem because the images were in different splits. It showed me that checking the dataset is important before training, especially to avoid having the same image in more than one split.



These duplicates still need to be fixed.



\## 4. Docker Smoke Test



For the Docker part, I built the image and started a container with `SKIP\_MODEL=1`.



I used this option because the goal was just to check if the API starts correctly, without loading the trained model.



After starting the container, I tested the `/health` endpoint.



I got:



`HTTP 200 - {"status":"ok"}`



I had a small problem at first because curl returned an empty reply on Windows. I tried again using `--noproxy` and IPv4, and the request worked.



So the Docker image was built successfully and the API was running.



\## 5. GitHub Actions



I created the workflow file `.github/workflows/ci.yml`.



I divided the pipeline into three jobs.



The first job, `test`, installs the dependencies and runs Ruff and pytest.



The second job, `smoke`, builds the Docker image, starts the container and checks the `/health` endpoint.



The last job, `push`, publishes the Docker image to GitHub Container Registry, but only for pushes to the `main` branch after the previous jobs pass.



The pipeline looks like this:



`Push / Pull Request → Test → Smoke → Push to GHCR (main only)`



I used the Git commit SHA as the Docker image tag so that each image can be linked to a specific version of the code.



For now, I tested Ruff, pytest and Docker locally. I still need to check the complete workflow on GitHub Actions.



\## 6. Model Promotion with MLflow



For model promotion, I used models that I had already trained in the previous labs.



I had version 1 registered as champion, and I registered another trained model as version 2 to test the promotion process.



The results were:



| Model | Version | Test accuracy |

|---|---|---|

| Champion | 1 | 64.55% |

| Candidate | 2 | 48.18% |



I created `promote.py` to decide if the candidate should replace the champion.



The rule was to compare the candidate accuracy with the champion accuracy plus two standard errors.



`SE = sqrt(p × (1 - p) / n)`



`Threshold = Champion accuracy + 2 × SE`



Here, `p` is the champion accuracy and `n` is the number of test images.



I used 220 test images.



I got these results:



\- Champion accuracy: 64.55%

\- Candidate accuracy: 48.18%

\- Standard error: 3.23%

\- Promotion threshold: 71.00%



Since the candidate accuracy was below 71%, it was not promoted.



The script returned:



`FAIL: Candidate assigned challenger alias`



I checked the aliases in MLflow and got:



`{'challenger': '2', 'champion': '1'}`



So version 1 stayed champion and version 2 became challenger. I also checked that the decision and both accuracy values were saved as tags in MLflow.



\## 7. What I Understood



The main difference between CI/CD and model promotion is what they check.



CI/CD checks the code and makes sure the application can run correctly. Model promotion checks the performance of the trained model.



For example, my candidate model could be used in an application that passes all the code tests, but that does not mean the model is better than the champion.



I also understood why the code version and model version are different. The Git commit SHA identifies the code used for the Docker image, while MLflow keeps track of the trained models using versions and aliases.



\## 8. Conclusion



In this lab, I added tests, data validation, Docker checks and model promotion to my Food11 project.



The five tests passed, Ruff found no remaining errors, and the Docker API returned HTTP 200.



The MLflow promotion script also worked. It kept version 1 as champion because the candidate did not reach the required accuracy.



The main problem I found was the duplicate images in the dataset. I still need to fix them and finish testing the GitHub Actions workflow through a Pull Request.

