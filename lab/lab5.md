# Lab 5 – CI/CD for Food11

## 1. Introduction

In this lab, I worked on CI/CD for my Food11 project. I used GitHub Actions to run tests automatically.

I also added data validation, tested Docker and worked on model promotion with MLflow.

The goal was to check my code before merging it into `main` and publish the Docker image automatically.

## 2. Code Changes and Testing

I started by changing `data.py`. I separated some parts of the preprocessing code into functions so I could test them more easily.

I also modified `serve.py`. I added `SKIP_MODEL=1` so the API can start without loading the real model.

Then I wrote tests for the data functions and the API.

I ran:

`py -m uv run --no-sync python -m pytest -q`

I got **5 passed, 4 warnings**.

The warnings were about deprecated functions. They did not stop the tests.

I also ran Ruff:

`py -m uv run --no-sync ruff check src tests`

Ruff found an import-order problem in `promote.py`.

I fixed it using:

`py -m uv run --no-sync ruff check src tests --fix`

After running Ruff again, I got `All checks passed!`.

## 3. Data Validation

I created `validate_data.py` to check the dataset before training.

The script checks five things:

1. All 11 classes are present in each split.
2. Images are RGB and have a size of 128×128.
3. Each class has enough images.
4. There are no duplicate images between splits.
5. Class proportions are similar between training and validation.

I tested the mini dataset with a minimum of 20 images per class.

Four checks passed, but the duplicate check failed.

I found two duplicate pairs:

- `evaluation/Seafood/8_100.jpg` and `validation/Seafood/8_102.jpg`
- `evaluation/Seafood/8_108.jpg` and `validation/Seafood/8_110.jpg`

### Testing the Duplicate Check

I also wanted to make sure the duplicate check worked correctly.

I copied an image from `training/Bread` into `evaluation/Bread`. I named it `lab5_duplicate_test.jpg`.

Then I ran the validation script again.

It detected the new duplicate and the two existing Seafood duplicates.

I deleted the temporary image and ran the script again. The Bread duplicate was gone.

The two Seafood duplicates are still present.

This test showed me that data validation can find problems that are not easy to notice manually.

## 4. Docker Smoke Test

I built the Docker image and started the API using `SKIP_MODEL=1`.

I used this option because I only wanted to check if the API starts correctly.

Then I tested the `/health` endpoint.

I got:

`HTTP 200 - {"status":"ok"}`

At first, curl returned an empty reply on Windows.

I tried again using `--noproxy` and IPv4. This time it worked.

The API was running correctly inside Docker.

## 5. GitHub Actions

I created `.github/workflows/ci.yml` to automate the testing process.

The workflow has three jobs:

- **test:** installs dependencies and runs Ruff and pytest.
- **smoke:** builds the Docker image, starts the API and checks `/health`.
- **push:** publishes the image to GHCR after the previous jobs pass on `main`.

I used the Git commit SHA to tag the image.

I pushed my changes to the branch `feature/lab5-ci-cd`.

GitHub Actions started automatically. Both `test` and `smoke` passed.

### Pull Request and Branch Protection

I opened Pull Request #1 to merge my changes into `main`.

I also created a ruleset called `Protect main branch`.

I added the Pull Request requirement and the `test` and `smoke` checks.

### Testing a CI Failure

I wanted to see what happens when a test fails.

I added this temporary test:

```python
def test_ci_failure():
    assert 1 == 2
```

I committed and pushed it to GitHub.

The `test` job failed, and `smoke` was skipped.

After that, I removed the failing test and pushed again.

Both jobs passed. I then merged the Pull Request into `main`.

### Publishing the Docker Image

After the merge, GitHub Actions ran on `main`.

All three jobs passed.

| Job | Result | Duration |
|---|---|---|
| test | Passed | 31 seconds |
| smoke | Passed | 1 min 43 sec |
| push | Passed | 3 min 48 sec |

The whole workflow took about 6 minutes and 12 seconds.

The Docker image was published to GHCR.

Image:

`ghcr.io/aliharkous123/mlops-lab-1`

Tag:

`545dc7fbaa4ab39185f944be4a050f31185de383`

I also downloaded the image on my laptop using `docker pull`.

The download completed successfully.

### Testing CI Caching

I created an empty commit to run the workflow again without changing the code.

The second workflow took 2 minutes and 7 seconds.

The `test` job went from 31 seconds to 27 seconds.

Dependency installation took 4 seconds in the second run.

Caching may have helped. The total time was also shorter because the `push` job did not run on the feature branch.

## 6. Model Promotion with MLflow

I created `promote.py` to decide if a candidate model should replace the champion.

The script compares the candidate accuracy with the champion accuracy.

I used this rule:

`SE = sqrt(p × (1 - p) / n)`

`Threshold = Champion accuracy + 2 × SE`

Here, `p` is the champion accuracy and `n` is the number of test images.

I used 220 test images.

The champion was version 1 with an accuracy of 64.55%.

I trained two new models using the mini dataset. Each model was trained for one epoch.

I changed the learning rate between the two runs.

My results were:

| Model | Learning rate | Test accuracy |
|---|---|---:|
| Champion v1 | 0.0001 | 64.55% |
| Candidate v4 | 0.00001 | 8.64% |
| Candidate v5 | 0.0001 | 21.82% |

I registered the new models as versions 4 and 5 in MLflow.

Then I ran `promote.py` on both versions.

The standard error was 3.23%, and the promotion threshold was 71.00%.

Both candidates failed the quality gate.

For both runs, the script returned:

`FAIL: Candidate assigned challenger alias`

Version 1 stayed champion. Version 5 became challenger because I tested it last.

The promotion script also saved the decision and accuracy values as model version tags.

The second model performed better than the first one. However, its accuracy was still below the champion.

## 7. Lab Questions and Answers

### Question 1 — Why is it a bad idea for a unit test to load the real model from MLflow?

Loading the real model takes time.

The test may fail if the MLflow server is offline or the model file is missing.

The code could be correct, but the test would still fail.

Using a fake model makes testing faster and easier.

### Question 2 — What does the fake model test prove?

It checks if the API can receive an image and return valid JSON.

It also checks that the category is Bread and the confidence is between 0 and 1.

It does not prove that the real model is accurate or makes correct predictions.

### Question 3 — Which check detects duplicates? Why are they dangerous?

The duplicate check detects the same image in different splits. It compares file hashes.

A train/test duplicate is dangerous because the model may have already seen the image during training.

This can make the test accuracy look higher than it really is.

A corrupted image usually causes an error. A duplicate may go unnoticed.

### Question 4 — Where should data validation run if GitHub Actions cannot access the dataset?

It can run locally before training.

It can also run in a data pipeline or on a runner that has access to the DVC dataset.

Both options help detect problems before training.

### Question 5 — What happens if a unit test fails?

The `smoke` job depends on `test` using `needs: test`.

If a unit test fails, `smoke` is skipped.

Without `needs`, both jobs could run independently.

The Docker build might continue even if the tests fail.

### Question 6 — How long did the workflow take? Which step got faster, and why?

My first successful workflow on `main` took 6 minutes and 12 seconds.

I ran the workflow again using an empty commit. It took 2 minutes and 7 seconds.

The `test` job went from 31 seconds to 27 seconds.

Dependency installation took 4 seconds in the second run.

Caching may have helped by reusing dependencies.

The total time was also shorter because the `push` job was skipped on the feature branch.

### Question 7 — Why use the commit SHA instead of `latest`?

The commit SHA identifies the exact code version.

The `latest` tag can change.

For example, one computer downloads `latest` on Monday. Another downloads it on Tuesday after a new release.

They might get different code.

Using the commit SHA avoids this problem.

### Question 8 — Why does the push job declare permissions?

The job needs permission to publish the Docker image to GHCR.

I used `contents: read` and `packages: write`.

This limits what the GitHub token can do.

If a compromised step had too many permissions, it could modify files, change workflows or publish unwanted packages.

### Question 9 — What happened when the test failed in the Pull Request?

GitHub showed a red failed check.

The `test` job failed, and `smoke` was skipped.

I configured branch protection to require passing checks before merging.

This helps teams detect problems automatically instead of depending only on local testing.

After removing the failing test, all checks passed.

I then merged the Pull Request.

### Question 10 — What did the promotion gate decide?

I trained two new models with different learning rates.

I registered them as versions 4 and 5.

I used 220 test images.

| Model | Learning rate | Test accuracy | Decision |
|---|---|---:|---|
| Champion v1 | 0.0001 | 64.55% | Remained champion |
| Candidate v4 | 0.00001 | 8.64% | Failed |
| Candidate v5 | 0.0001 | 21.82% | Failed |

The standard error was 3.23%.

Two standard errors represent about 6.45 percentage points.

The promotion threshold was 71.00%.

Both candidates failed the gate.

Version 1 stayed champion, and version 5 became challenger.

### Question 11 — How can model promotion run automatically?

One solution is to use a hosted MLflow server, such as DagsHub.

GitHub Actions could access it after training.

Another solution is to use a self-hosted runner that can access the local MLflow server.

Both solutions can run `promote.py` automatically after training.

### Question 12 — Draw the complete pipeline.

```text
Developer changes code             [Human]
          |
          v
Git push / Pull Request             [Human]
          |
          v
GitHub Actions starts               [Automatic]
          |
          v
Ruff + pytest                       [Automatic]
          |
          v
Docker build + smoke test           [Automatic]
          |
          v
Review and merge Pull Request       [Human]
          |
          v
GitHub Actions runs on main         [Automatic]
          |
          v
Build and publish image to GHCR     [Automatic]
          |
          v
Image tagged with Git commit SHA    [Automatic]
          |
          v
Pull and deploy the image           [Human]
          |
          v
Running container
```

The Git commit SHA identifies the code version.

The model version is selected separately in MLflow using the `champion` alias.

I ran model promotion manually with `promote.py`. The script checks accuracy and updates the alias.

The CI smoke test starts a test container automatically. The final deployment is still a separate manual step.

## 8. What I Understood

CI/CD checks the code and the application. Model promotion checks the performance of the trained model.

Even if the code passes all tests, the model may still have low accuracy.

I also understood the difference between code versions and model versions.

Git uses the commit SHA to identify the code. MLflow uses versions and aliases to manage models.

The failing test showed me why CI and branch protection are useful.

Data validation was also important because it found duplicate images that I did not notice before.

## 9. Conclusion

In this lab, I added automated tests, data validation, Docker checks and model promotion.

The five tests passed. Ruff also passed, and the Docker API returned HTTP 200.

GitHub Actions detected an intentional test failure. After removing it, the checks passed again.

I merged the Pull Request into `main`. The Docker image was published to GHCR, and I downloaded it successfully.

I also trained two new models and tested the promotion gate. Both candidates failed, so version 1 stayed champion.

The two original Seafood duplicates are still present in the dataset.

This lab helped me understand how automated testing, Docker and MLflow work together.