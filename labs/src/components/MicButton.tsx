import './MicButton.css'
import React, { useState, useImperativeHandle, forwardRef } from 'react'

interface MicButtonProps {
    src_img: string;
    onToggleOn: () => void;
    onToggleOff: () => void;
}

type Props = MicButtonProps & React.HTMLAttributes<HTMLButtonElement>; // can include both custom props but also standard react props like

export interface MicButtonHandle {
    disable: () => void;
}

const MicButton = forwardRef<MicButtonHandle, Props>(({src_img, onToggleOn, onToggleOff, className, ...rest}, ref) => {
    // state
    const [isActive, setIsActive] = useState(false); // state
    const [isDisabled, setIsDisabled] = useState(false); // state 

    const handleClick = () => {
        if (isDisabled) return

        if (!isActive) {
            onToggleOn();
        }
        else {
            onToggleOff();
        }
        setIsActive((prev) => !prev);
    }

    useImperativeHandle(ref, () => ({
        disable: () => {
          setIsDisabled(true);
          setIsActive(false); // set visually off
          console.log("Mic button disabled permanently");
        },
    }));

    return(
        <button 
            // any additional classes, plus the container class
            className={`micbutton_container ${isActive ? 'toggled' : ''} ${isDisabled ? 'disabled' : ''} ${className || ''}`}
            onClick={handleClick}
            {...rest}
        > 
            <img src={src_img} className="micbutton_logo" alt="microphone logo" />
        </button>
    );
})

export default MicButton