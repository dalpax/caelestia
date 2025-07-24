if status is-interactive
    # Starship custom prompt
    starship init fish | source

    # Custom colours
    cat ~/.local/state/caelestia/sequences.txt 2> /dev/null

    # For jumping between prompts in foot terminal
    function mark_prompt_start --on-event fish_prompt
        echo -en "\e]133;A\e\\"
    end
end

# Created by `pipx` on 2025-06-26 07:11:48
set PATH $PATH /home/dalpax/.local/bin
alias peaclock="peaclock --config-dir ~/.config/peaclock"
