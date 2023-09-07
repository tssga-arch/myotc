# kurotc: Restricted OTC Tool

Restricted automation script

```{argparse}
   :filename: ../src/urotc.py
   :func: cliparser
```

- kurotc:
  - document roles
  - to test, limiting scope, in IAM, create a project in a specific region.  Create
    resources in project.  specify project_name in kurocfg


Under IAM->Permissions.
Create Policy/Role with:

```javascript
    {
        "Version": "1.1",
        "Statement": [
            {
                "Action": [
                    "ecs:*:get*",
                    "ecs:*:list*",
                    "ecs:*:stop*",
                    "ecs:*:start*",
                    "ecs:*:reboot*"
                ],
                "Effect": "Allow"
            }
        ]
    }
```

Create a Project to contain the restricted resources

- Create a new group for users with restricted access.
- Click on the authorize action for the groiup.  Select the restricted role.  Click next and
  change from "all resources" to region-specific projets.  Select the project containing restricted resources.
- https://docs.otc.t-systems.com/python-otcextensions/install/configuration.html



