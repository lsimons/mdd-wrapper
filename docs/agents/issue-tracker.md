# Issue tracker: GitHub

Issues for this project are managed as GitHub issues on
[`lsimons/mdd-wrapper`](https://github.com/lsimons/mdd-wrapper/issues),
which is also where pull requests go.

That remote is not necessarily named `origin` in a given clone, so pass
the repository explicitly rather than relying on the default:

```bash
gh issue list   --repo lsimons/mdd-wrapper
gh issue create --repo lsimons/mdd-wrapper --label needs-triage
```

You can learn about the `gh` issue CLI with `gh issue --help`.

Do not file a security vulnerability as an issue; see
[`SECURITY.md`](../../SECURITY.md) for the private reporting route.

## Labels

The following issue labels are used:

```
NAME              DESCRIPTION                                     COLOR
bug               Something isn't working                         #d73a4a
documentation     Improvements or additions to documentation      #0075ca
duplicate         This issue or pull request already exists       #cfd3d7
enhancement       New feature or request                          #a2eeef
good first issue  Good for newcomers                              #7057ff
help wanted       Extra attention is needed                       #008672
invalid           This doesn't seem right                         #e4e669
needs-info        Waiting on reporter for more information        #e6e6fa
needs-triage      Maintainer needs to evaluate this issue         #e6e6fa
question          Further information is requested                #d876e3
ready-for-agent   Fully specified, ready for an autonomous agent  #e6e6fa
ready-for-human   Requires human implementation                   #e6e6fa
wontfix           This will not be worked on                      #ffffff
```

The five lavender labels drive triage: a new issue arrives
`needs-triage`, and leaves it as `needs-info`, `ready-for-agent`,
`ready-for-human` or `wontfix`.
