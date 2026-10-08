import React from 'react'
import styles from "./sideBar.module.css";
import ArticleIcon from '@mui/icons-material/Article';
const Sidebar = () => {
  return (
    <div className={styles.sideBar}>
            <div className={styles.sideBarIcon}>
                <ArticleIcon sx={{ fontSize: 54, marginBottom: 2 }} />
                <div className={styles.sideBarTopContent}>Resume Screening</div>
            </div>

            <div className={styles.sideBarOptionsBlock}></div>
            </div>
  )
}

  
export default Sidebar;