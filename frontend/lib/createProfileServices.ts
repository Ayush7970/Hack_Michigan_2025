import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8100',
});

export const createProfile = async (
    message: string
) => {

    try{
        const response = await fetch('http://localhost:8100/rest/post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
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

