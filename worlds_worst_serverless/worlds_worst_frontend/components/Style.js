import React from "react";

const Style = () => (
    <style jsx>{`
      * {
        margin: 0;
        padding: 0;
        background-color: #000000;
      }
      .container {
        min-height: 100vh;
        padding: 0 0.5rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
      }

      main {
        padding: 5rem 0;
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: top;
        align-items: center;
        color: #778d96;
      }

      .title {
        margin: 0;
        line-height: 2;
        font-size: 4rem;
      }

      .description {
        line-height: 1.5;
        font-size: 1.5rem;
      }
      
      .actions {
        line-height: 1.5;       
        font-size: 1.5rem;
      }
      
      input {
          background-color: #000000;
          border: none;
          font-family: sans-serif;
          color: #778d96;
          padding: 30px 32px;
          text-align: center;
          text-decoration: none;
          display: inline-block;
          font-size: 20px;
          outline-width: 0;
        }
        
        ::placeholder { /* Chrome, Firefox, Opera, Safari 10.1+ */
            color: #778d96;
            opacity: 0.5; /* Firefox */
        }
        :-ms-input-placeholder { /* Internet Explorer 10-11 */
             color: #778d96;
        }
        ::-ms-input-placeholder { /* Microsoft Edge */
            color: #778d96;
        }

      @media (max-width: 600px) {
        .grid {
          width: 100%;
          flex-direction: column;
        }
      }
    `}</style>
);

export default Style;