### Usage
Integrate all steps needed before releasing a study
- clean up outdated gene symbols / entrez IDs
- calculate TMB score

### Before running 

Set global environment variables
Add following lines to `~/.bash_profile` and `~/.profile`, then restart any console sessions.
```
export DATAHUB_HOME=[absolut-path-to-datahub-repo]
export DATAHUB_TOOL_HOME=[absolut-path-to-datahub-tool-repo]
```

### Notes

For studies with `CVR TMB` (subsetted from IMPACT) remove `CVR TMB`
