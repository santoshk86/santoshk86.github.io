---
title: 'Refactoring and Code Quality in .NET: Analyzers, Sonar, Style, and Architecture Tests'
date: 2026-04-04
permalink: /posts/2026/04/refactoring_code_quality_dotnet/
tags:
  - dotnet
  - code-quality
  - refactoring
  - analyzers
  - architecture
  - advanced
---

This post covers practical code quality tools and refactoring habits for .NET teams: **Roslyn analyzers, formatting rules, Sonar, architecture tests, and safe refactoring workflows**. Code quality is not about making code look clever. It is about making change safer and cheaper.

Refactoring vs rewriting
------
Refactoring changes internal structure without changing external behavior. Rewriting replaces implementation more broadly.

Good refactoring:
- has tests or clear verification
- happens in small steps
- preserves behavior
- improves naming, boundaries, or duplication

Risky refactoring:
- changes too many behaviors at once
- mixes cleanup with feature work
- lacks tests around the affected paths
- moves code without improving clarity

Refactoring should reduce future cost, not create churn.

Roslyn analyzers
------
Roslyn analyzers inspect C# code at compile time.

Common analyzer categories:
- correctness
- style
- security
- performance
- API usage

Enable built-in analysis in `.csproj`:

```xml
<PropertyGroup>
  <AnalysisLevel>latest</AnalysisLevel>
  <TreatWarningsAsErrors>false</TreatWarningsAsErrors>
</PropertyGroup>
```

For mature projects, teams often turn selected warnings into errors.

EditorConfig
------
`.editorconfig` keeps formatting and style consistent.

Example:

```ini
[*.cs]
dotnet_style_qualification_for_field = false:suggestion
csharp_style_namespace_declarations = file_scoped:suggestion
dotnet_diagnostic.IDE0060.severity = warning
```

Consistent formatting reduces review noise. Developers should discuss design, behavior, and risk instead of whitespace.

Sonar and static analysis
------
SonarQube or SonarCloud can identify:
- bugs
- vulnerabilities
- code smells
- duplication
- test coverage gaps

Use static analysis as a signal, not as a substitute for engineering judgment. Not every finding has equal value, and suppressions should be intentional.

Architecture tests
------
Architecture tests verify dependency rules.

Example rule:

```text
Domain must not depend on Infrastructure.
```

Conceptual test:

```csharp
[Fact]
public void Domain_Should_Not_Depend_On_Infrastructure()
{
    var result = Types.InAssembly(typeof(Order).Assembly)
        .Should()
        .NotHaveDependencyOn("Store.Infrastructure")
        .GetResult();

    Assert.True(result.IsSuccessful);
}
```

Architecture tests are useful when boundaries are important and easy to accidentally violate.

Refactoring workflow
------
A safe workflow:
1. add or confirm tests around the behavior
2. make one structural change
3. run tests
4. repeat
5. keep commits focused

For large refactors, avoid mixing:
- renames
- behavior changes
- dependency upgrades
- formatting-only changes

Separate commits make review and rollback easier.

Code review signals
------
Look for:
- unclear names
- hidden side effects
- duplicated business rules
- missing error handling
- weak tests around changed behavior
- abstractions with no clear purpose

Do not chase theoretical purity while ignoring real bugs. Code quality should support delivery and reliability.

Common mistakes to avoid
------
Watch for these issues:
- treating analyzer output as a checklist without judgment
- doing broad cleanup in unrelated feature PRs
- creating abstractions before duplication proves they are needed
- ignoring architecture drift until it is expensive to fix
- refactoring without a way to verify behavior

Sustainable code quality comes from small habits repeated consistently: clear names, focused tests, useful analyzers, architecture boundaries, and disciplined refactoring.

------------------------------------------------------------------------

**Next Article:** Building Production-Ready .NET Systems: A Practical Roadmap
