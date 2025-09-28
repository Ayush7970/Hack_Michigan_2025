import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8001',
});

export const sendInput = async (
    input:string, address:string
) => {
    console.log("🔥 SERVICE: sendInput called");
    console.log("📨 Input:", input);
    console.log("🎯 Address:", address);

    const payload = {
        input: input,
        address: address
    };
    console.log("📦 Payload:", JSON.stringify(payload, null, 2));

    try{
        console.log("🌐 Making fetch request to http://localhost:8001/rest/post");

        const response = await fetch('http://localhost:8001/rest/post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        console.log("📊 Response status:", response.status);
        console.log("📊 Response ok:", response.ok);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("📄 Response data:", data);
        return data;
    }catch(err){
        console.error("💥 SERVICE: Error in sendInput:", err);
        return null;
    }
}

export const getConversation = async () => {
    try{
        const response = await fetch('http://localhost:8001/conversation', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
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

