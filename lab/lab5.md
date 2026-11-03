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

### Question 1
**Why is it a bad idea for a unit test to load the real model from your MLflow server? List at least two ways the test could fail even though your code is correct.**

Loading the real model is slow and needs the MLflow server to be running. The test could fail if the server is offline or if there is a connection problem. It could also fail if the model file is missing, even when my code is correct. This is why I used a fake model for testing.

### Question 2
**The fake model always answers "Bread" with 0.90 confidence. What exactly does `test_predict_returns_valid_json` prove, and what does it *not* prove?**

This test checks that the API can receive an image and return a JSON response with the right information. It checks that the category is Bread and that the confidence is between 0 and 1. It does not tell us if the real model is accurate or if it can predict other food classes correctly.

### Question 3
**Which check caught it? Why is a train/test duplicate more dangerous than a corrupted image, even though the corrupted image makes the training script crash and the duplicate does not?**

The duplicate check found the copied image by comparing MD5 hashes between the dataset splits.

A duplicate between training and testing is a problem because the model may have already seen that image. This can make the accuracy look better than it really is. A corrupted image usually gives an error, but a duplicate can stay in the dataset without anyone noticing.

### Question 4
**Your CI runner cannot see your data (it is in DVC, and maybe in a local remote). Where in your workflow should `validate_data.py` run so that it still protects you? Give two places.**

I can run `validate_data.py` on my computer before training because I have the dataset locally. I can also run it on a self-hosted runner that has access to the DVC data. This way, the dataset is checked before starting training.

### Question 5
**The `smoke` job has `needs: test`. What happens to it if a unit test fails? What would happen without `needs`?**

If a unit test fails, the smoke job is skipped because it depends on the test job. Without `needs: test`, the smoke job could still run even if the tests failed.

### Question 6
**How long did the whole run take? Run it a second time (push an empty commit with `git commit --allow-empty -m "ci"`) and compare. Which step got faster, and why?**

The first successful workflow on `main` took 6 minutes and 12 seconds.

I ran the workflow again using an empty commit. The second run took 2 minutes and 7 seconds.

The test job became a little faster, going from 31 seconds to 27 seconds. Dependency installation took 4 seconds in the second run. Caching may have helped by reusing dependencies.

The second workflow was also shorter because the push job did not run on the feature branch.

### Question 7
**This answers Question 9 of Lab 3. Why tag with the commit SHA rather than `latest`? Describe a concrete situation where `latest` leads two machines to run different code.**

The commit SHA tells us exactly which code version was used to build the Docker image.

For example, if I download an image tagged `latest` today and someone updates it tomorrow, another computer downloading `latest` could get different code. Using the commit SHA avoids this because each image has a specific version.

### Question 8
**Why does the `push` job declare `permissions:` explicitly? What could a compromised step do with a token that had write access to everything in the repo?**

The push job needs permission to upload the Docker image to GHCR. I used `contents: read` and `packages: write` so the token only has the permissions needed for this job.

If a compromised step had full access, it could change repository files, modify workflows or publish unwanted packages.

### Question 9
**What does the pull request page show? Could you still merge? What does that change for a team compared to "everybody runs the tests on their laptop before pushing"?**

When I added a failing test, GitHub showed a red failed check. The test job failed, and the smoke job was skipped.

The required checks were not passing, so the Pull Request was not ready to merge. After fixing the test, both checks passed and I merged it.

For a team, this is useful because GitHub runs the same checks automatically. We do not have to depend only on each person remembering to test the code on their laptop.

### Question 10
**For each candidate, what did the gate decide, and with which numbers? With your test-set size, how many accuracy points does `2 * se` represent?**

I trained two new models using different learning rates and registered them in MLflow as versions 4 and 5. I used 220 images for testing.

| Model | Learning rate | Test accuracy | Decision |
|---|---|---:|---|
| Champion v1 | 0.0001 | 64.55% | Stayed champion |
| Candidate v4 | 0.00001 | 8.64% | Failed |
| Candidate v5 | 0.0001 | 21.82% | Failed |

The standard error was about 3.23%, so `2 * se` represents about 6.45 percentage points.

The candidate needed at least 71.00% accuracy to replace the champion. Both candidates were below this value, so version 1 stayed champion. Version 5 became challenger because I tested it last.

### Question 11
**`promote.py` needs to reach your MLflow server, so it cannot run in GitHub's cloud runners while MLflow lives on your laptop. Name two ways to make it run automatically after training. (Hint: DagsHub also offers a hosted MLflow server per repository.)**

One way is to use a hosted MLflow server like DagsHub. GitHub Actions could access it and run `promote.py` after training.

Another way is to use a self-hosted runner that can connect to my local MLflow server. Both options would let the promotion script run automatically.

### Question 12
**Draw (in `lab/lab5.md`) the pipeline you now have, from `git push` to a running container. Mark which steps are automatic, which still need a human, and where the code version and the model version are decided.**

```text
Developer writes code                 [Manual]
          |
          v
Git push / Pull Request               [Manual]
          |
          v
GitHub Actions starts                 [Automatic]
          |
          v
Ruff + pytest                         [Automatic]
          |
          v
Docker build + smoke test             [Automatic]
          |
          v
Review and merge Pull Request         [Manual]
          |
          v
GitHub Actions runs on main           [Automatic]
          |
          v
Build and push image to GHCR          [Automatic]
          |
          v
Image tagged with Git commit SHA      [Automatic]
          |
          v
Pull and run Docker image             [Manual]
          |
          v
Running container
```

The code version is identified by the Git commit SHA used for the Docker image.

The model version is managed separately in MLflow using the `champion` alias.

I ran `promote.py` manually to compare the candidate models with the champion. Both candidates failed the quality gate, so version 1 stayed champion.

The smoke test runs a temporary container automatically, but running the final published image is still a manual step.

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