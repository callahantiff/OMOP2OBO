# loinc2hpoAnnotation
This repo holds data generated from the loinc2hpo app! There are two default folders:

**Task**: holds lists of LOINC codes awaiting annotating;

**Data**: holds annotation data

# Set up
1. clone this repo to your local machine.
2. start loinc2hpo
3. specify this loinc2hpoAnnotation as the default folder for auto-save.
4. import default data by clicking `File`-`Open session`, choose loinc2hpoAnnotation/Data and click ok.

**check your configurations**

Click `Configuration`-`Show Settings`, you should see "<*path*>/loinc2hpoAnnotation" in line "Path to auto-saved file", and "<*path*>/loinc2hpoAnnotation/Data" in line "Path to last session". <*path*> is dependent on where you cloned loinc2hpoAnnotation on your computer.  

# Annotation
The **Task** folder contains LOINC lists that need to be annotated. Use the `filter` button to start annotating those LOINC codes. When you are done, save your session data and check in your data. We adopt a similar model with HPO in that only one person is allowed to edit the file at one time. So remember to send out an email to loinc2hpoannotation@googlegroups.com (example, LOCKING loinc2hpo as the subject) to let people know that you are locking/unlocking the files.

1. Let people know that you are locking the files. 
2. From terminal, use $cd command to enter loinc2hpoAnnotation folder
3. Pull the most recent annotation file from Github. 
```
$ git checkout develop
$ git pull origin develop
```
   Please work on the "develop" branch. 

4. Do Step 2 and 3 before you launch loinc2hpo. Now, start working on a *task*: click **Filter**, choose **loinc2hpoAnnotation**/**Task**/**UNC-loinc1.txt**. After you are done, save your session data. 

5. Execute the following command:
```
$ git add .
$ git commit -m "YOUR MESSAGE"
$ git push origin develop
```
repace "YOUR MESSAGE" with your commit comment. 

6. Let people know that you have unlocked the files. 

# Annotating with newly created HPO terms
The issues is that we are updating the main hp.obo and hp.owl files about once a month, and so the files that the Loinc biocuration app automaticxally pulls fgrom the net will not contain newly created HPO terms until the next release. However, we can locally create up-to-date copies of these files as follows.

1. Create new HPO term with Protege as usual
2. Create up-to-date version of hp.obo and hp.owl as follows.

**(3, 4 only need to be done once)**

3. Building owltools

We need to download and build owltools. The GitHub repository can be found here: https://github.com/owlcollab/owltools.git. Clone the repository and build it as follows.
```
$ git clone https://github.com/owlcollab/owltools.git
$ cd owltools
$ ./build.sh
```

You need to change the owltools to executables:
 go to owltools directory, run
```
$ chmod +x OWLTools-Oort/bin/*
$ chmod +x OWLTools-Runner/bin/*
```

4. Update your path with the following command (assuming you have a directory called GIT on the first level of your home directory and have cloned owltools there; otherwise adjust!).
```
$ export PATH=${HOME}/GIT/owltools/OWLTools-Oort/bin/:${HOME}/GIT/owltools/OWLTools-Runner/bin/:$PATH
```
(this can be added to .bashrc / .bash_profile on the Mac)

Restart your terminal

5. Go to the HPO, run 
```
git pull
```
enter human-phenotype-ontology/src/ontology and then enter "$ make". This will make a new version of the hp.obo and the hp.owl files in that directory.

6. Set the path to the new hp.obo and hp.owl files in the loinc2hpo biocuration app . Click **"Configuration"** - **"Change hpo.owl"** to set the path to your hpo.owl file; use the button below to set the path to the hpo.obo file. 
(This step only needs to be done once unless you have pointed those file somewhere else)

The newly created hp owl and obo files are under the src/ontology folder. 

7. You should now be able to create a Loinc mapping with the new HPO term.

# Reset loinc2hpo settings
If you cannot launch loinc2hpo, it is probably some configurations are set incorrectly. The easiest way is to delete the configuration file under
{HOME}/.loinc2hpo

Detele the loinc2hpo.settings file by running:
```
rm loinc2hpo.settings
```
Then try launching loinc2hpo again. It will ask you to reset all the configurations. 
