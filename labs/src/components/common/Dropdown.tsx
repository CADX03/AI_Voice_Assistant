import './Dropdown.css'
import * as Constants from '../../constants/index.ts'
import { useEffect, useRef, useState } from 'react';
import Icon from '../Icon.tsx';

interface DropdownProps {
    options: string[];
    optionsIcons: string[];
    onChange?: (index: number) => void; // callback function when an option is selected
    gradient?: boolean;
    menuOffset?: number; // horizontal offset of dropdown menu from the input line
    isClickable?: boolean; // determine if dropdown is clickable
    initialConfigs?: number; // initial selected option - if we want dropdown to be independent in state management
    selectedConfigs?: number; // selected index - if we want dropdown state to be controlled by parent
}

interface SelectionModalProps {
    onSelectOption: (index: number) => void;
    currentSelected: number;
}

const Dropdown: React.FC<DropdownProps> = ({
    options, 
    optionsIcons, 
    onChange,
    gradient=false, 
    // menuOffset=-12,
    isClickable=true,
    initialConfigs=0,
    selectedConfigs
}) => {

    const [isSelectionOpen, setSelectionOpen] = useState(false);
    const [internalSelected, setInternalSelected] = useState(initialConfigs);

    // selected value depends on in if component is controlled from parent or independent
    const optionSelected = selectedConfigs !== undefined ? selectedConfigs : internalSelected;
    
    const handleToggleSelection = () => {
        if (isClickable) {
            setSelectionOpen((prev) => !prev);
        }
    }

    const handleSelectOption = (index: number) => {
        //only update state if the dropdown is not controlled by parent
        if (selectedConfigs === undefined) {
            setInternalSelected(index);
        }
        setSelectionOpen(false);

        if (onChange) { // callback function when an option is selected
            onChange(index);
        }
    }

    // Close dropdown when clicking outside
    const dropdownRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {// on load page
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setSelectionOpen(false);
            }
        };
        
        document.addEventListener('mousedown', handleClickOutside);
        return () => { // on unmount
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);
    
    //panel that shows the options, when the dropdown is opened
    const SelectionModal: React.FC<SelectionModalProps> = ({ onSelectOption, currentSelected}) => (
        <div className="selection_div" 
            // style={{left: `${menuOffset}vw`}}
        >
            {options.map((option, index) => (
                <div key={index} 
                    className={`selection_option ${index === currentSelected ? 'selected' : ''}`}
                    onClick={() => onSelectOption(index)}
                >
                    <Icon 
                        className="icon_dropdown"
                        altName={options[index]}
                        icon={optionsIcons[index]}
                        size={1.2}
                    />
                    <span className={`dropdown_text ${index === currentSelected ? 'selected' : ''}`}>{option}</span>
                </div>
            ))}
        </div>
    );
    
    // main dropdown component
    // if the dropdown is not clickable, it will only show the selected option
    if (!isClickable) {
        return (
            <div className="dropdown_display">
                <div className="line_left_container">
                    <Icon 
                        className="icon_dropdown"
                        altName={options[optionSelected]}
                        icon={optionsIcons[optionSelected]}
                        size={1.2}
                    />
                    <span className="dropdown_display_text">
                        {options[optionSelected]}
                    </span>
                </div>
            </div>
        )
    }
    // if the dropdown is clickable, it will show the selected option and a button to open the dropdown
    return(
        <div className="dropdown_container" ref={dropdownRef}>
            <div 
                className={`input_line ${gradient ? 'gradient' : ''}`} 
                onClick={handleToggleSelection}
            >
                <div className="line_left_container">
                    <Icon 
                        className="icon_dropdown"
                        altName={options[optionSelected]}
                        icon={optionsIcons[optionSelected]}
                        size={1.2}
                    />
                    <span className={`line_text ${gradient ? 'gradient' : ''}`}> {options[optionSelected]}</span>
                </div>
                <Icon 
                    className="line_right_container icon_dropdown"
                    altName="Dropdown button"
                    icon={isSelectionOpen ? Constants.icons.dropup_arrow_blue : Constants.icons.dropdown_arrow_black}
                    size={1.2}
                />
            </div>
            {isSelectionOpen && 
                <SelectionModal 
                    onSelectOption={handleSelectOption}
                    currentSelected={optionSelected}
                />
            }
        </div>
    );
}

export default Dropdown