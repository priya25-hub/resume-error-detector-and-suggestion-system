import { useState } from 'react'
import heroImg from './assets/hero.png'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import './App.css'
import Sidebar from "./component/sidebar/sidebar";

function App() {
  const [count, setCount] = useState(0)

  return (
     <div className='App'>
      <Sidebar />
    </div>
 

    
  )
}

export default App
