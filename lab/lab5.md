\# Lab 5 – CI/CD for Food11



\## 1. Introduction



In this lab, I added CI/CD to my Food11 project. I used GitHub Actions to run tests automatically.



I also worked on data validation, Docker testing and model promotion with MLflow.



\## 2. Code Changes and Testing



I started by modifying `data.py`. I separated the preprocessing code into functions to make testing easier.



I also changed `serve.py` so the API can start without loading the model. For this, I used `SKIP\_MODEL=1`.



Then I wrote tests for the data functions and the API.



I ran:



`uv run --no-sync python -m pytest -q`



Result: \*\*5 passed, 4 warnings\*\*.



The warnings were related to deprecated functions. They did not affect the tests.



I also checked the code with Ruff:



`uv run --no-sync ruff check src tests`



Ruff found an import-order error in `promote.py`. I fixed it using:



`uv run --no-sync ruff check src tests --fix`



I ran Ruff again and got `All checks passed!`.



\## 3. Data Validation



I created `validate\_data.py` to check the dataset before training.



The script checks five things:



1\. All 11 classes are present in each split.

2\. Images are RGB and have a size of 128×128.

3\. Each class has enough images.

4\. There are no duplicate images between splits.

5\. The class distribution is balanced.



I tested the mini dataset with a minimum of 20 images per class.



Four checks passed, but the duplicate check failed.



I found two duplicate pairs:



\- `evaluation/Seafood/8\_100.jpg` and `validation/Seafood/8\_102.jpg`

\- `evaluation/Seafood/8\_108.jpg` and `validation/Seafood/8\_110.jpg`



I did not expect to find duplicates between the splits. This showed me why data validation is important.



The duplicates still need to be fixed.



\## 4. Docker Smoke Test



I built the Docker image and started the API with `SKIP\_MODEL=1`.



This allowed me to test the API without loading the trained model.



Then I tested the `/health` endpoint.



Result:



`HTTP 200 - {"status":"ok"}`



At first, curl returned an empty reply on Windows. I tried again with `--noproxy` and IPv4, and it worked.



The API was running correctly inside Docker.



\## 5. GitHub Actions



I created `.github/workflows/ci.yml` to automate the checks.



The workflow has three jobs:



\- \*\*test:\*\* installs dependencies and runs Ruff and pytest.

\- \*\*smoke:\*\* builds Docker, starts the API and checks `/health`.

\- \*\*push:\*\* publishes the Docker image to GHCR after a successful push to `main`.



The pipeline is:



`Push / Pull Request → Test → Smoke → Push to GHCR (main only)`



I used the Git commit SHA to tag the Docker image.



I pushed my changes using the branch `feature/lab5-ci-cd`.



GitHub Actions started automatically. Both `test` and `smoke` passed.



\### Pull Request and Branch Protection



I opened Pull Request #1 from `feature/lab5-ci-cd` to `main`.



I created a branch protection ruleset called `Protect main branch`.



I enabled the Pull Request requirement and added `test` and `smoke` as required checks.



This means the checks must pass before merging.



\### Testing a CI Failure



I added a temporary failing test:



```python

def test\_ci\_failure():

&#x20;   assert 1 == 2

```



I committed and pushed the test to GitHub.



GitHub Actions detected the error. The `test` job failed, and `smoke` was skipped.



Then I removed the failing test and pushed again.



This time, both jobs passed on the push and Pull Request workflows.



I saw how CI can detect errors before merging.



\## 6. Model Promotion with MLflow



I used two models from my previous labs.



Version 1 was the champion. I registered another model as version 2 to test the promotion.



My results were:



| Model | Version | Test accuracy |

|---|---|---|

| Champion | 1 | 64.55% |

| Candidate | 2 | 48.18% |



I created `promote.py` to compare the models.



The candidate must reach the champion accuracy plus two standard errors.



`SE = sqrt(p × (1 - p) / n)`



`Threshold = Champion accuracy + 2 × SE`



Here, `p` is the champion accuracy and `n` is the number of test images.



I used 220 test images.



The results were:



\- Champion accuracy: 64.55%

\- Candidate accuracy: 48.18%

\- Standard error: 3.23%

\- Promotion threshold: 71.00%



The candidate did not reach the threshold.



The script returned:



`FAIL: Candidate assigned challenger alias`



I checked MLflow and got:



`{'challenger': '2', 'champion': '1'}`



Version 1 stayed champion, and version 2 became challenger.



I also checked that MLflow saved the decision and accuracy values as tags.



\## 7. What I Understood



CI/CD checks the code and the application. Model promotion checks if a new model is better than the current one.



Even if the code passes all tests, the model may still have lower accuracy.



The Git commit SHA identifies the Docker image version. MLflow uses model versions and aliases.



I also tested branch protection. When I added a failing test, GitHub Actions detected it. After removing the test, the checks passed again.



\## 8. Conclusion



In this lab, I added automated tests, data validation, Docker checks and model promotion.



The five tests passed. Ruff also passed, and the Docker API returned HTTP 200.



I tested GitHub Actions with a Pull Request. The pipeline detected a failing test and passed again after I removed it.



MLflow kept version 1 as champion because version 2 had lower accuracy.



I still need to fix the duplicate images and merge the Pull Request.

