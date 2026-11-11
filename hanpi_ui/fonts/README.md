Hanpi bundles the Latin variable fonts used by its English interface so the app
and sign-in page do not depend on Google Fonts being reachable. Chinese uses the
device's existing Chinese font fallback.

- Fredoka: `@fontsource-variable/fredoka` 5.3.0, `files/fredoka-latin-wght-normal.woff2`.
- Plus Jakarta Sans: `@fontsource-variable/plus-jakarta-sans` 5.3.0, `files/plus-jakarta-sans-latin-wght-normal.woff2`.

Source: https://www.npmjs.com/package/@fontsource-variable/fredoka and
https://www.npmjs.com/package/@fontsource-variable/plus-jakarta-sans.
Both use the SIL Open Font License; their full original licences are included.
The fonts are embedded in CSS so the authentication screen can load them without
accessing protected app files. No runtime download or Node installation is needed.
