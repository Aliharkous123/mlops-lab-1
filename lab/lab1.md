\# Lab 1 ali harkous - Git, DVC and Data Preparation



\## Question 1



After running "uv init", several project files were created.  

`pyproject.toml` contains the project information and dependencies.  

`.python-version` specifies the Python version used by the project.  

`README.md` is used to document the project.



\## Question 2



Running `dvc init` created the `.dvc` folder and `.dvcignore`.



The `.dvc` folder contains DVC configuration files needed to manage the data versions.  

`.dvcignore` is similar to `.gitignore` and tells DVC which files or folders it should ignore.



The non-secret DVC configuration files should be pushed to Git so that another developer can reproduce the project configuration.



\## Question 3



The location of the DVC configuration depends on the option used. With `--global`, the configuration is stored globally for the user. Other possibilities include repository-level configuration and `--local`.



Credentials should not be pushed to GitHub because they contain private authentication information. For this lab, credentials can be kept in the local DVC configuration.



\## Question 4



After running `dvc add data`, DVC added the data directory to `.gitignore`.



This prevents Git from storing the actual dataset. The dataset is managed by DVC instead, while Git only tracks the DVC pointer file.



\## Question 5



Yes, a `data.dvc` file was created.



It contains information that DVC uses to identify the version of the data, such as a hash and information about the tracked directory. It acts as a pointer to the data managed by DVC.



\## Question 6



On GitHub, I can see the project files and the `data.dvc` pointer, but the actual image dataset is not stored directly in Git.



The actual data is stored in the DVC remote on DagsHub. On the DagsHub interface, I can access the DVC-tracked data.



\## Question 7



After cloning the GitHub repository into a new temporary folder, the `data` folder was not initially available because Git only downloaded the code and DVC pointer.



I used:



`dvc pull`



to retrieve the actual data from the DVC remote. After the pull, the `data` folder was restored with `food11\_raw`, `food11\_processed`, and `food11\_processed\_mini`.



\## Question 8



No. After checking out the previous Git commit and running `dvc checkout`, the `food11\_processed` and `food11\_processed\_mini` folders disappeared and only `food11\_raw` remained.



After switching back to `main` and running `dvc checkout` again, the processed folders came back. This shows that Git versions the DVC pointer while DVC restores the corresponding version of the data.


## DagsHub upload workaround

I had difficulties pushing the full Food-11 dataset to DagsHub because of the large data size and connection interruptions.

I used solution 2 (Reduce the data folder size). I kept the same data structure but used a smaller number of images from each category. The full dataset was stored separately outside the Git repository.

After reducing the dataset size, I was able to push the data successfully using DVC.

