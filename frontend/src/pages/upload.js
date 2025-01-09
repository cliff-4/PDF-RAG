// pages/upload.js
import { useState, useEffect } from "react";
import axios from "axios";
import { Formik, Form, Field } from "formik";
import "../app/globals.css";

const NEXT_PUBLIC_BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

const btomb = (num) => {
    // Bytes to MB, at most 1 decimal place
    return Math.round(num / 1e5) / 10;
};

const convoFormat = (item) => {
    let c = "bg-red-600 mb-4";
    if (item[0] === "0") {
        c = "bg-blue-600";
    }
    let d = " w-fit rounded-lg p-2";
    return c + d;
    // return c;
};

const reloadPage = () => {
    window.location.reload();
};

const FileUploadPage = () => {
    const [fileCount, setFileCount] = useState(0);
    const [totalSize, setTotalSize] = useState(0);
    const [convo, setConvo] = useState([]);
    const [sources, setSources] = useState([]);

    useEffect(() => {
        let c = localStorage.getItem("convoHistory");
        if (c === null) c = "[]";
        console.log(`Setting convo to ${c}`);
        if (c) {
            c = JSON.parse(c);
        }
        setConvo(c);
    }, []);

    const syncConvo = (newConvo) => {
        let x = JSON.stringify(newConvo);
        localStorage.setItem("convoHistory", x);
        setConvo(newConvo);
        console.log(`Synced convo to ${x}`);
    };

    const handleFileUpload = async (values) => {
        const formData = new FormData();
        values.files.forEach((file) => {
            formData.append("files", file);
        });

        try {
            const response = await axios.post(
                `${NEXT_PUBLIC_BACKEND_URL}/upload`,
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );
            alert(response.data.message);
            // reloadPage();
        } catch (error) {
            console.error("An error occured: " + error);
            alert(error);
        }
    };

    const handleQuery = async (values) => {
        const formData = new FormData();
        formData.append("inputValue", values.inputValue);
        let newConvo = [...convo, ["0", values.inputValue]];

        try {
            const response = await axios.post(
                `${NEXT_PUBLIC_BACKEND_URL}/ask`,
                {
                    inputValue: values.inputValue,
                }
            );
            newConvo = [...newConvo, ["1", response.data.response]];
            syncConvo(newConvo);
            setSources(response.data.sources);
            alert("Response generated!");
        } catch (error) {
            console.error("Error handling query:", error);
            alert("Error handling query");
        }
    };

    const clearFiles = async () => {
        try {
            const response = await axios.post(
                `${NEXT_PUBLIC_BACKEND_URL}/clearfiles`,
                {
                    password: "poopybutthole",
                }
            );
            alert(response.data.msg);
        } catch (error) {
            console.error("Error clearing files:", error);
            alert("Error clearing files");
        }
    };

    useEffect(() => {
        const fetchFileData = async () => {
            try {
                const countResponse = await axios.get(
                    `${NEXT_PUBLIC_BACKEND_URL}/files/count`
                );
                const sizeResponse = await axios.get(
                    `${NEXT_PUBLIC_BACKEND_URL}/files/size`
                );
                setFileCount(countResponse.data.pdf_files_count);
                setTotalSize(sizeResponse.data.total_size_bytes);
            } catch (error) {
                console.error("Error fetching file data:", error);
            }
        };

        fetchFileData();
    }, []);

    return (
        <div className="w-full p-10 flex flex-col gap-4">
            <p className="text-5xl w-full text-center m-4">Upload PDF File</p>
            <div className="flex flex-row justify-around">
                <div className="border-2 rounded-lg p-4">
                    <Formik
                        initialValues={{ files: [] }}
                        onSubmit={(values, { resetForm }) => {
                            handleFileUpload(values);
                            resetForm();
                        }}
                    >
                        {({ setFieldValue }) => (
                            <Form className="bg-gray-800 text-white py-2 px-4 rounded-md">
                                <input
                                    type="file"
                                    accept=".pdf"
                                    multiple
                                    onChange={(event) => {
                                        const files = Array.from(
                                            event.currentTarget.files
                                        );
                                        setFieldValue("files", files);
                                    }}
                                />
                                <button
                                    type="submit"
                                    className="bg-blue-500 text-white rounded py-2 px-4 hover:bg-blue-600"
                                >
                                    Upload
                                </button>
                            </Form>
                        )}
                    </Formik>
                    <div>
                        <p className="text-xl">File System Information</p>
                        <p>Number of PDF files: {fileCount}</p>
                        <p>Total size of PDF files: {btomb(totalSize)} MB</p>
                        <p className="w-full flex flex-row justify-between mt-2">
                            <a
                                className="bg-blue-500 text-white rounded py-2 px-4 hover:bg-blue-600"
                                href={`${NEXT_PUBLIC_BACKEND_URL}/fileserver`}
                                target="_blank"
                            >
                                View files
                            </a>
                            <button
                                className="bg-red-500 text-white rounded py-2 px-4 hover:bg-red-600"
                                onClick={() => {
                                    clearFiles();
                                    // reloadPage();
                                }}
                            >
                                Clear files
                            </button>
                        </p>
                    </div>
                </div>
                <div className="flex flex-col justify-center">
                    <Formik
                        initialValues={{ inputValue: "" }}
                        onSubmit={(values, { resetForm }) => {
                            handleQuery(values);
                            resetForm();
                        }}
                    >
                        {() => (
                            <Form className="flex flex-col border-2 rounded-lg gap-4 p-4">
                                <div className="w-full">
                                    <Field
                                        name="inputValue"
                                        type="text"
                                        placeholder="ask me anything!"
                                        className="border rounded p-2 w-full text-gray-700"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="bg-blue-500 text-white rounded py-2 px-4 hover:bg-blue-600"
                                >
                                    Submit
                                </button>
                            </Form>
                        )}
                    </Formik>
                </div>
            </div>
            <div className="border-2 rounded-lg p-4 flex flex-col gap-4">
                <p className="w-full text-4xl text-center">Conversation</p>
                <ul className="gap-2">
                    {convo.map((item, index) => (
                        <li key={index} className={convoFormat(item)}>
                            {item[1]}
                        </li>
                    ))}
                </ul>
                <div className="flex flex-row gap-4 items-center">
                    {sources.length === 0 ? (
                        <></>
                    ) : (
                        <span className="flex-none text-2xl">Sources:</span>
                    )}
                    <div className="grow flex flex-row gap-2">
                        {sources.map((item, key) => (
                            <a
                                key={key}
                                href={item}
                                target="_blank"
                                className="text-white bg-blue-500 hover:bg-blue-600 py-1 px-2 rounded-lg"
                            >
                                {"Ref " + (key + 1)}
                            </a>
                        ))}
                    </div>
                    <button
                        className="flex-none bg-red-500 text-white rounded py-2 px-4 hover:bg-red-600"
                        onClick={() => {
                            setConvo([]);
                            setSources([]);
                            syncConvo([]);
                        }}
                    >
                        Clear
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FileUploadPage;
