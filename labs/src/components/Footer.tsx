import { useEffect, useState } from 'react';
import './Footer.css'

function Footer() {
    return(
        <div className="footer_container">
            <footer>
                <span className='footer_text'> &copy; Voice Future {new Date().getFullYear()}</span>
            </footer>
        </div>
    )
}

export default Footer;