# Taskmaster Configuration Attributes

## Process Configuration Attributes

### cmd (attribute)
**Required** - The command to execute when starting the process.

#### Format:
- String containing the full command with arguments
- Can include absolute or relative paths
- Arguments should be space-separated

#### Example:
```yaml
cmd: "/usr/bin/python3 /app/server.py --port 8080"
```

---

### numprocs (attribute)
Controls how many instances of this process to start.

#### Allowed values:
- Positive integer (default: `1`)
- Each instance will have a unique process identifier

#### Example:
```yaml
numprocs: 4  # Start 4 instances of this process
```

---

### umask (attribute)
Sets the umask for the process (file creation permissions mask).

#### Allowed values:
- Octal notation (e.g., `022`, `077`)
- Default: inherits from parent process

#### Example:
```yaml
umask: 022  # Standard umask for most services
```

---

### workingdir (attribute)
Sets the working directory for the process.

#### Allowed values:
- Absolute path to directory
- Directory must exist and be accessible
- Default: inherits from taskmaster process

#### Example:
```yaml
workingdir: "/app/myservice"
```

---

### autostart (attribute)
Controls whether the process starts automatically when taskmaster starts.

#### Allowed values:
- `true`: Start automatically (default)
- `false`: Only start when explicitly requested

#### Example:
```yaml
autostart: true
```

---

### autorestart (attribute)
Controls whether the process should be restarted automatically when it exits.

#### Allowed values:
- `true`: Always restart, no matter how it exits
- `false`: Never restart
- `unexpected`: Restart only if the exit code is not listed in `exitcodes`

#### Example:
```yaml
autorestart: unexpected
```

---

### exitcodes (attribute)
List of exit codes that are considered "expected" (successful termination).

#### Allowed values:
- List of integers
- Default: `[0]`
- Used with `autorestart: unexpected`

#### Example:
```yaml
exitcodes: [0, 2]  # 0 and 2 are considered successful exits
```

---

### startretries (attribute)
Number of attempts to start the process before giving up.

#### Allowed values:
- Non-negative integer
- Default: `3`
- `0` means infinite retries

#### Example:
```yaml
startretries: 5  # Try starting up to 5 times
```

---

### startsecs (attribute)
Minimum time (in seconds) the process must stay running to be considered successfully started.

#### Allowed values:
- Positive integer or float
- Default: `1`
- Prevents rapid restart cycles

#### Example:
```yaml
startsecs: 10  # Process must run for 10 seconds to be considered started
```

---

### stopsignal (attribute)
Signal to send to the process when requesting it to stop.

#### Allowed values:
- Signal name (e.g., `TERM`, `INT`, `KILL`, `USR1`)
- Signal number (e.g., `15`, `9`, `10`)
- Default: `TERM`

#### Example:
```yaml
stopsignal: TERM  # Send SIGTERM for graceful shutdown
```

---

### stoptsecs (attribute)
Maximum time (in seconds) to wait for the process to stop before sending SIGKILL.

#### Allowed values:
- Positive integer
- Default: `10`
- After this timeout, SIGKILL is sent

#### Example:
```yaml
stoptsecs: 30  # Wait 30 seconds before force killing
```

---

### stdout (attribute)
Configuration for capturing and redirecting standard output.

#### Allowed values:
- `null`: Discard output
- File path: Redirect to file
- `AUTO`: Auto-generate log file name
- Dict with options: `{file: "path", maxbytes: 1000000, backups: 3}`

#### Example:
```yaml
stdout:
  file: "/var/log/myapp.log"
  maxbytes: 10000000  # 10MB
  backups: 5          # Keep 5 backup files
```

---

### stderr (attribute)
Configuration for capturing and redirecting standard error.

#### Allowed values:
- Same options as `stdout`
- `STDOUT`: Redirect stderr to same destination as stdout

#### Example:
```yaml
stderr: STDOUT  # Combine stderr with stdout
```

## Configuration File Example

```yaml
programs:
  webapp:
    cmd: "/usr/bin/python3 /app/webapp.py"
    numprocs: 2
    workingdir: "/app"
    autostart: true
    autorestart: unexpected
    exitcodes: [0]
    startretries: 3
    startsecs: 5
    stopsignal: TERM
    stoptsecs: 15
    stdout:
      file: "/var/log/webapp.log"
      maxbytes: 50000000
      backups: 10
    stderr: STDOUT
    umask: 022
```

## Notes
- All attributes are optional except `cmd`
- Boolean values should be lowercase (`true`/`false`)
- File paths should be absolute for reliability
- Log rotation is automatic when `maxbytes` and `backups` are specified


