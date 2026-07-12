# Localization
Because there are many different services with disparate architectures, localization is handled centrally in the files in `resources/lang/`. The translations in these files are then copied to their appropriate projects through the use of the `resources/lang/build.py` script.

### Defining a translated string
To create a localized resource string, go to the appropriate language file in `resources/lang` and add a key with the following syntax:

```yaml
path.to.key @dest1 @dest2 @dest3: Translated text
```

When `build.py` is run, `path.to.key: Translated text` will be copied to `@dest1`, `@dest2`, and `@dest3`. You can specify as many destinations as you want; if none are specified, the translation will be sent to all targets. You can use any of the following targets:

- `@be`: used by backend services (system error logs, etc.). Note that most errors, such as when a user's account cannot be created, should be tagged in the frontend, since the backend has no knowledge of a user's language preference.
- `@web`: used in the Signosure Web UI.
- `@app`: used in the Android or iOS data collection app.

### Filling in values
Sometimes we need to fill in values in a text translation. You can specify
values using `{variable}`, which should match the variable in your code:

```yaml
users.reg.code.invalid @web @app: The registration code {reg_code} is not valid.
```


### Pluralization
In some cases, we need to pluralize text. You can use the syntax `{ref:}`, where `ref` is the JSON key you will use to point to translations. Each key in the reference should be an integer, an integer range (`a..b` or `a...b`), or `else` for the base translation, as shown here:

```yaml
users.login.locked-out @web @app: 
  text: Please try logging in again after {h:} and {m:}.
  h:
    1: 1 hour
    else: '{h} hours'
  m:
    1: 1 minute
    else: '{m} minutes'
```

If no pluralization is required, you can simply provide the translation directly:

```yaml
users.login.locked-out @web @app: 
  text: Please try logging in again after {h:} and {m:}.
  h: 
    1: '{h} hr'
    else: '{h} hrs'
  m: '{m} min'
```

### Usage
To use the localized strings, you can import the `t(key, substitutions, locale)` function with a dictionary containing the substituted values:

```py
from lib.l10n import t

translated = t('users.login.locked-out', { 'h': 2, 'm': 30 })
# > "Please try logging in again after 2 hours and 30 minutes."
```

```ts
import { t } from './lib/l10n';

const translated = t('users.login.locked-out', { h: 2, m: 30 }, 'ja-JP');
// 
```
