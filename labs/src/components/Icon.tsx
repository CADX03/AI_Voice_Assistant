
interface IconProps {
    onClick?: () => void;
    onEnterHover?: () => void;
    onLeaveHover?: () => void;
    altName: string,
    icon: string,
    size?: number;
    cursor?: boolean;
    backgroundColor?: string;
}

type Props = IconProps & React.HTMLAttributes<HTMLButtonElement>; // can include both custom props but also standard react props like
const Icon: React.FC<Props> = ({altName, icon, onClick=() => {}, onEnterHover=()=>{}, onLeaveHover=()=>{}, size=2, backgroundColor, className, cursor=true, ...rest}) => {
    
    const styles = {
        icon_container: {
            backgroundColor: backgroundColor || 'transparent',
            border: 'none',
            cursor: cursor ? 'pointer' : 'default',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            outline: 'none',
            borderRadius: '50%',
            margin: 0,
            padding: 0
        },

        icon_logo: {
            width: `${size}em`,
            height: `${size}em`
        }

    }

    return(
        <button 
            className={`${className || ''}`}
            style={styles.icon_container} 
            onClick={onClick}
            onMouseEnter={onEnterHover}
            onMouseLeave={onLeaveHover}
            {...rest}
        >
            <img src={icon} style={styles.icon_logo} className="icon_logo" alt={altName} />
        </button>
    );

}

export default Icon