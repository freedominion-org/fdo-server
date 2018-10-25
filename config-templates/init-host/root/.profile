PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:~/bin; export PATH
HOME=/root; export HOME
TERM=${TERM:-xterm}; export TERM
PAGER=less; export PAGER
EDITOR=vim; export EDITOR
tabs -4
LESS="--tabs=4"; export LESS
MORE="--tabs=4"; export MORE

# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
        . "$HOME/.bashrc"
    fi
fi
