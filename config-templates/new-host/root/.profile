PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:~/bin ; export PATH
HOME=/root ; export HOME
TERM=${TERM:-xterm} ; export TERM
PAGER=less ; export PAGER
EDITOR=vi ; export EDITOR

# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
        . "$HOME/.bashrc"
    fi
fi
