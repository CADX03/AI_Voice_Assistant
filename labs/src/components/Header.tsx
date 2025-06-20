import './Header.css';
import * as Constants from '../constants/index.ts';
import { Link } from 'react-router-dom';

interface HeaderProps {
    rightContent?: React.ReactNode;
    isHeaderAtTop: boolean; // change style based on scroll position
}

const Header: React.FC<HeaderProps> = ({ rightContent = null, isHeaderAtTop }) => {
    return (
        <header className={`header_container ${isHeaderAtTop ? 'scrolled' : ''}`}>
            <div className="header_left">
                
                <Link to="/" className={`header_company_text ${isHeaderAtTop ? 'scrolled' : ''}`}>Voice Future</Link>
                <img
                    src={Constants.icons.soundwave}
                    className={`header_company_logo ${isHeaderAtTop ? 'scrolled' : ''}`}
                    alt="Voice Future logo"
                />
            </div>

            <div className="header_center1">
                <Link to="/use-cases" className={`header_company_text ${isHeaderAtTop ? 'scrolled' : ''}`}>Use Cases</Link>
            </div>
            <div className="header_center2">
                <Link to="/about" className={`header_company_text ${isHeaderAtTop ? 'scrolled' : ''}`}>About us</Link>
            </div>
                 
            <div className="header_right">
                {rightContent}
            </div>
        </header>
    );
}

export default Header;