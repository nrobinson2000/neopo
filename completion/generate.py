from neopo.command import commands, iterable_commands, legacy_commands

print(r'''# neopo(1) completion
# depends on jq(1)

_find_toolchains() {
    [ -n "$NEOPO_PATH" ] && [ -d "$NEOPO_PATH/toolchains" ] && echo "$NEOPO_PATH/toolchains" && return
    [ -n "$NEOPO_LOCAL" ] && [ -d "$HOME/.local/share/neopo/toolchains" ] && echo "$HOME/.local/share/neopo/toolchains" && return
    [ -d "$HOME/.particle/toolchains" ] && echo "$HOME/.particle/toolchains" || exit
}

_find_cache() {
    [ -n "$NEOPO_PATH" ] && [ -d "$NEOPO_PATH/resources/cache" ] && echo "$NEOPO_PATH/resources/cache" && return
    [ -n "$NEOPO_LOCAL" ] && [ -d "$HOME/.local/share/neopo/resources/cache" ] && echo "$HOME/.local/share/neopo/resources/cache" && return
    [ -d "$HOME/.neopo/cache" ] && echo "$HOME/.neopo/cache" || exit
}

_project() {
    local _projects
    local _dir

    for _dir in $PWD/*/; do
        if [ -f "${_dir}project.properties" ]; then
            _projects="${_projects} $(basename $_dir)"
        fi
    done

    COMPREPLY=($(compgen -W  "$_projects" -- "$cur"))
}

_get_versions() {
    local _versions _dir _installed
    _versions=$(jq -r .[].version $(_find_cache)/firmware.json)

    for _dir in $(_find_toolchains)/deviceOS/*/; do
        [ "$(basename $_dir)" != '*' ] && _installed="$(basename $_dir)\n${_installed}"
    done

    [ -z $_installed ] && _versions=$(echo "${_versions}" | sort -V | uniq) || _versions=$(echo -e "${_installed}${_versions}" | sort -V | uniq)

    COMPREPLY=($(compgen -W  "$_versions" -- "$cur"))
}

_run() {
    local _targets _buildscripts
    _buildscripts=$(jq -r .buildscripts $(_find_cache)/manifest.json)
    _targets=$(grep '.PHONY' $(_find_toolchains)/buildscripts/$_buildscripts/Makefile)
    _targets="${_targets#.PHONY: *}"
    COMPREPLY=($(compgen -W  "$_targets" -- "$cur"))
}

_configure() {
    local _platforms _cache
    _cache=$(_find_cache)
    _platforms=$(jq -r .[].name $_cache/platforms.json | tr '\n' ' ' && echo)
    COMPREPLY=($(compgen -W  "$_platforms" -- "$cur"))
}

_neopo() {
    local _options _iterable cur prev prev1 prev2

    _options="%s"
    _iterable="%s"

    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD - 1]}"
    prev1="${COMP_WORDS[COMP_CWORD - 2]}"
    prev2="${COMP_WORDS[COMP_CWORD - 3]}"

    if [ "$COMP_CWORD" == 1 ]; then
        COMPREPLY=($(compgen -W "$_options" -- "$cur"))
        return 0
    fi

    if [ "$COMP_CWORD" == 2 ] && [ "$prev" == "help" ]; then
        COMPREPLY=($(compgen -W "$_options" -- "$cur"))
        return 0
    fi

    if [ "$prev1" == "run" ] || [ "$prev1" == "export" ]; then
        _project
        return 0
    fi

    if [ "$prev1" == "configure" ]; then
        _get_versions
        return 0
    fi

    if [ "$prev2" == "configure" ]; then
        _project
        return 0
    fi

    if [ "$prev1" == "create" ]; then
        _configure
        return 0
    fi

    if [ "$prev2" == "create" ]; then
        _get_versions
        return 0
    fi

    if [ "$prev" == "bootloader" ]; then
        _configure
        return 0
    fi

    if [ "$prev1" == "bootloader" ]; then
        _get_versions
        return 0
    fi

    local legacy_options="serial dfu"
    local legacy_options2="open close"

    if [ "$prev" == "legacy" ]; then
        COMPREPLY=($(compgen -W "$legacy_options" -- "$cur"))
        return 0
    fi

    if [ "$prev1" == "legacy" ] && [[ $legacy_options =~ "$prev" ]]; then
        COMPREPLY=($(compgen -W "$legacy_options2" -- "$cur"))
        return 0
    fi

    case "$prev" in
    create|compile|build|flash|flash-all|clean|settings|libs)
        _project;;
    run|export)
       _run;;
    configure)
        _configure;;
    get)
        _get_versions;;
    script)
        COMPREPLY=($(compgen -f -- "$cur"));;
    iterate)
        COMPREPLY=($(compgen -W "$_iterable" -- "$cur"));;
    esac
} &&
complete -F _neopo neopo''' % (" ".join(commands.keys()), " ".join(iterable_commands.keys())))
