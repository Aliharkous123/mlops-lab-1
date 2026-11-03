# Lab 5 – Questions and Answers

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
