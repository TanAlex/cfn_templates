# README

in the CodeBuild spec.
```
            post_build:
              commands:
                - docker push "$IMAGE_URI"
                - printf '{"ImageUri":"%s"}' "$IMAGE_URI" > build.json
          artifacts:
            files: build.json
```

The last `artifacts` statement tells the output is the build.json

Later, in the final deploy section
```
                ParameterOverrides: !Sub |
                  {
                    "EnvironmentName": "${EnvironmentName}",
                    "ImageUrl": {
                      "Fn::GetParam" : ["BuildOutput", "build.json", "ImageUri"]
                    }
                  }
              InputArtifacts:
                - Name: Source
                - Name: BuildOutput
```
The ImageUrl uses `"Fn::GetParam" : ["BuildOutput", "build.json", "ImageUri"]` to get the value from the `build.json`