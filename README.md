
To create a new package change the version number in the setup.py file and run the following:
` python3 setup.py sdist `
a tar.gz will be created at ./dist folder


move the tar.gz file created to ./external/packages and run:
` pipenv install ./external/packages/{package-name} `

push the code with the updated Pipefile and Pipefile.clock

do it for EA1 and EA2 repos

