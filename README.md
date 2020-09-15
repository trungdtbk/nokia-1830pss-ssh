# A ssh library for CLI/root shell on Nokia 1830-PSS Network Elements

## Install

pip install nokia1830pss

## Usage

### CLI interaction
```
from pss1830ssh.pss1830cli import PSS1830Cli

cli = PSS1830Cli('10.0.0.1', 22, 'admin', 'admin')
cli.open()
cli.execute('show version')
cli.execute('show card inv *')
cli.close()
```

### Root interaction
```
from pss1830ssh.pss1830root import PSS1830Root

# Execute command on the master shelf, active EC
root = PSS1830Root('10.0.0.1', 22, 'root', 'root')
root.open()
root.execute('ps -ef')

# Execute command on standby EC of the master shelf
root.login_to_stdby()
root.execute('ps -ef')
root.logout_from_stdby()

# Execute command on the active EC of a shelf without knowing which one
root.login_to_shelf(shelf=2)
root.execute('ps -ef')
root.logout_from_shelf()

# Execute command on the active EC of a shelf assuming the active EC is EC 2/1
root.login_to_shelf(shelf=2, ec=1)
root.execute('ps -ef')
root.logout_from_shelf()

# Execute command on a specific EC of a shelf
root.login_to_shelf(shelf=3, ec=18, act=False)
root.execute('ps -ef')
root.logout_from_shelf()

# Execute command on a slot
root.login_to_slot(shelf=1, slot=3)
root.execute('ps -ef')
root.logout_from_slot()

root.close()
```
