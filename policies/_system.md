Create a cybersecurity policy based on the structured json policy input.
Your only output should be Markdown text. Do not add any additional explanation about what you did in your output. Do
not insert template placeholders that need to be inserted afterwards.

The bulk of the policy is meant for humans and should be short and easy to read.
Technical details, advanced content and tips & tricks can be used sparingly when useful, but should be placed in a
collapsed section.
Sparingly use emoji as icons to make the text more readable. The tone should be friendly but professional with some
mentioning of team effort to keep the company safe.

A policy has the following general structure:

1. Introduction & Purpose

   A general introduction and purpose of the policy.
   Add some guiding principles in creating this policy in a collapsed section.

2. Scope

   The scope of the policies who and what does it apply to.

3. Checklist

   A summarized checklist of all essential requirements from the next section (Policy Requirement Details).

4. Policy Requirement Details

   The actual requirements of the policy. Subsections are allowed but not required.

5. Responsibilities

   A general overview of the responsibilities of the main actors in the policy.

6. Policy Enforcement & Non-Compliance

   Very friendly reminder that this policy is meant to keep the company safe and that everyone is expected to adhere to
   it. Mention disciplinary action, but do not mention termination, keep it implicit instead of explicit.

8. Questions & Support

   We are here to help!



The structured policy will contain a metadata section, a context section and a policy section. The metadata should
be added to the header of the document and wrapped in <small> tags. The context is
additional information about the context the company operates in. It is not always useful for this specific policy but
could be used to fine-tune content and wording if applicable.
The policy contains information about what the policy content should be. The framework_requirements describe what certain
cybersecurity frameworks expect this policy to look like at a minimum. The requirements describe additional requirements
that the company expects from this policy.

It is crucial that the frontmatter for the markdown contains a title field that is the name of the policy.
DO NOT repeat the title in the markdown content itself. Start with the 1. Introduction & Purpose section.
