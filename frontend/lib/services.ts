import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8080',
});

export const sendInput = async (
    message: string
) => {

    try{
        const response = await fetch('http://localhost:8080/match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description: message,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    }catch(err){
        console.log(err);
        return null;
    }
}