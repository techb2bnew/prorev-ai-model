--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: damage_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.damage_types (
    class_key character varying(50) NOT NULL,
    display_name character varying(100) NOT NULL,
    description text,
    model_label character varying(60),
    model_class_index integer,
    color_hex character varying(9),
    is_critical boolean NOT NULL,
    is_active boolean NOT NULL,
    sort_order integer NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.damage_types OWNER TO postgres;

--
-- Name: detections; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detections (
    inspection_id uuid NOT NULL,
    inspection_image_id uuid NOT NULL,
    damage_type_id uuid NOT NULL,
    confidence numeric(5,4) NOT NULL,
    severity character varying(20) NOT NULL,
    bbox_x integer,
    bbox_y integer,
    bbox_width integer,
    bbox_height integer,
    polygon jsonb,
    area_ratio numeric(7,6),
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.detections OWNER TO postgres;

--
-- Name: inspection_images; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inspection_images (
    inspection_id uuid NOT NULL,
    cloudinary_public_id character varying(255) NOT NULL,
    secure_url text NOT NULL,
    thumbnail_url text,
    view_angle character varying(20),
    width integer,
    height integer,
    file_size_bytes bigint,
    format character varying(10),
    sequence_no integer NOT NULL,
    status character varying(20) NOT NULL,
    failure_reason text,
    quality_report jsonb,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.inspection_images OWNER TO postgres;

--
-- Name: inspections; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inspections (
    user_id uuid NOT NULL,
    reference_code character varying(40) NOT NULL,
    status character varying(20) NOT NULL,
    overall_severity character varying(20) NOT NULL,
    damage_score integer NOT NULL,
    total_detections integer NOT NULL,
    total_area_percent double precision NOT NULL,
    damage_summary jsonb,
    model_name character varying(100),
    model_version character varying(50),
    processing_completed_at timestamp with time zone,
    processing_ms integer,
    error_code character varying(60),
    error_message text,
    idempotency_key character varying(120),
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    detection_preset character varying(20),
    detection_settings jsonb,
    below_threshold_count integer NOT NULL,
    model_backend character varying(40),
    customer_name character varying(150),
    vehicle_type character varying(40)
);


ALTER TABLE public.inspections OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(150),
    phone character varying(20),
    role character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: damage_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.damage_types (class_key, display_name, description, model_label, model_class_index, color_hex, is_critical, is_active, sort_order, id, created_at, updated_at) FROM stdin;
dent	Dent	Indentations, dings and sheet metal compressions.	dent	0	#38bdf8	f	t	1	5dced117-c5b2-4be6-91fb-a076a6ce0d21	2026-08-18 11:55:27.002547+05:30	2026-08-18 11:55:27.002547+05:30
scratch	Scratch	Paint abrasions, scrape lines and clear-coat scuffs.	scratch	1	#f59e0b	f	t	2	802cacb5-e296-4b62-8f5f-4fcbd34a6503	2026-08-18 11:55:27.007079+05:30	2026-08-18 11:55:27.007079+05:30
crack	Crack	Windshield fissures and bumper or fender cracks.	crack	2	#f43f5e	f	t	3	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	2026-08-18 11:55:27.009079+05:30	2026-08-18 11:55:27.009079+05:30
glass_shatter	Glass Shatter	Webbed breaks and shattered window panels.	glass shatter	3	#c084fc	t	t	4	a41cd314-1427-4003-a2b9-313216c56fd7	2026-08-18 11:55:27.010076+05:30	2026-08-18 11:55:27.010076+05:30
lamp_broken	Lamp Broken	Broken headlight, taillight or turn signal lenses.	lamp broken	4	#fde047	t	t	5	252cd10c-eb2d-4a8c-ac32-28a5af142a74	2026-08-18 11:55:27.012079+05:30	2026-08-18 11:55:27.012079+05:30
tire_flat	Tire Flat	Deflated tyre, punctured sidewall or exposed rim.	tire flat	5	#34d399	t	t	6	e4d231fc-562f-44f5-9f50-4e4c68c25266	2026-08-18 11:55:27.014076+05:30	2026-08-18 11:55:27.014076+05:30
\.


--
-- Data for Name: detections; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.detections (inspection_id, inspection_image_id, damage_type_id, confidence, severity, bbox_x, bbox_y, bbox_width, bbox_height, polygon, area_ratio, id, created_at, updated_at) FROM stdin;
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	b3c1425e-776f-40a7-81bc-ed57a2e56734	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.5712	severe	217	118	553	267	null	0.481663	b2791078-2b00-4e9a-99a9-20ab0d6b3793	2026-08-18 12:44:59.966679+05:30	2026-08-18 12:44:59.966679+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	76aae949-89b9-4565-a491-c9ec44fb0923	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	2cd0f9a1-21b3-4669-86f5-f5512272ad73	2026-08-18 12:45:03.83497+05:30	2026-08-18 12:45:03.83497+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	ac175af4-e8f5-453e-a5cc-ee0d0c49e7f6	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	16177583-f52b-47db-9244-41f8f2a26973	2026-08-18 12:45:07.279655+05:30	2026-08-18 12:45:07.279655+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	ac175af4-e8f5-453e-a5cc-ee0d0c49e7f6	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.4787	severe	34	248	268	98	null	0.131547	5ea32ac7-3fdc-4a47-998a-83e7069c9f5f	2026-08-18 12:45:07.279655+05:30	2026-08-18 12:45:07.279655+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	831c1497-13f3-4a93-818a-a1c50469cb97	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3884	moderate	251	337	199	91	null	0.059092	02f3b028-d76e-4c7d-8824-d06952c1cdc1	2026-08-18 12:45:10.510826+05:30	2026-08-18 12:45:10.510826+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dadaa205-d762-4b55-883f-dce322cb3299	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3066	severe	267	124	462	198	null	0.298411	ab999ade-2e6e-453f-b212-63fcc53c0fbb	2026-08-18 13:29:10.94124+05:30	2026-08-18 13:29:10.94124+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	0e40a25a-0cd4-47ba-b5ca-51dbcd7d27cb	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	d6278766-7304-420b-a936-f4e6c1d403c1	2026-08-18 13:29:13.869482+05:30	2026-08-18 13:29:13.869482+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	0e40a25a-0cd4-47ba-b5ca-51dbcd7d27cb	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.2505	severe	4	406	820	400	null	0.282675	18a70a98-174d-434b-9b88-a9adc5d54eea	2026-08-18 13:29:13.869482+05:30	2026-08-18 13:29:13.869482+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	209d7f94-3f02-4cbe-9179-f08b8f32821c	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	e70b80bb-b87c-42b0-b5eb-d3c3a240d478	2026-08-18 13:29:16.760004+05:30	2026-08-18 13:29:16.760004+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	209d7f94-3f02-4cbe-9179-f08b8f32821c	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.4787	severe	34	248	268	98	null	0.131547	9ba0398f-01db-481d-bd2c-dc1047d40891	2026-08-18 13:29:16.760004+05:30	2026-08-18 13:29:16.760004+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	32152275-4ba8-4a3d-9f54-9abd4c09a271	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3884	moderate	251	337	199	91	null	0.059092	99626d99-ee0a-4f6a-8a1d-1f154f55bcee	2026-08-18 13:29:19.703733+05:30	2026-08-18 13:29:19.703733+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	32152275-4ba8-4a3d-9f54-9abd4c09a271	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3037	minor	148	409	97	42	null	0.013294	55015128-5086-4385-9305-94f69e605e8a	2026-08-18 13:29:19.703733+05:30	2026-08-18 13:29:19.703733+05:30
074094a4-77af-408c-ab06-6eda073d3df8	b6b8ee05-8838-4f76-a97c-655f47d0d151	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	fc896b2c-0aac-4fd6-82bd-25c119efdda2	2026-08-18 13:31:33.941246+05:30	2026-08-18 13:31:33.941246+05:30
074094a4-77af-408c-ab06-6eda073d3df8	b6b8ee05-8838-4f76-a97c-655f47d0d151	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.2505	severe	4	406	820	400	null	0.282675	3bcc79d0-b4a7-4365-83d8-7417b5dd6894	2026-08-18 13:31:33.941246+05:30	2026-08-18 13:31:33.941246+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	610f294b-4b90-499a-8b32-93ddabe4ed6b	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	1cc19474-4452-4a61-a846-1b27b5018dbc	2026-08-18 13:32:32.456464+05:30	2026-08-18 13:32:32.456464+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	a3e066b5-8aba-4e2d-be33-485ca76e361f	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	08ec4bf4-a71b-42ef-9e85-c1a9d3e6719c	2026-08-18 16:22:53.561988+05:30	2026-08-18 16:22:53.561988+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	d41fc5b7-4b31-4220-91a8-abd94c433865	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	01b48011-c016-48bb-9912-19533cdbe5de	2026-08-18 16:22:57.975871+05:30	2026-08-18 16:22:57.975871+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	d41fc5b7-4b31-4220-91a8-abd94c433865	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.4787	severe	34	248	268	98	null	0.131547	bb55b640-90e4-4959-b0ba-3b7c5248c38e	2026-08-18 16:22:57.975871+05:30	2026-08-18 16:22:57.975871+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	4974153c-05e9-4171-84f2-6f950b163d22	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3884	moderate	251	337	199	91	null	0.059092	addd21f0-4e26-4be3-b8e9-d32ad7d0328b	2026-08-18 16:23:01.423813+05:30	2026-08-18 16:23:01.423813+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	0020b111-0adb-4e04-a807-b4fbe7226233	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3066	severe	267	124	462	198	null	0.298411	0887fd89-0b02-431e-a1f8-406630e327d8	2026-08-18 16:27:44.364518+05:30	2026-08-18 16:27:44.364518+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	db644740-6b72-4998-adaa-52d04816f7f2	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	4711a599-10d7-4336-8031-9e9cfec09b76	2026-08-18 16:27:47.825149+05:30	2026-08-18 16:27:47.825149+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	db644740-6b72-4998-adaa-52d04816f7f2	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.2505	severe	4	406	820	400	null	0.282675	297c372d-c02d-4f2f-b07c-7aa379cd2383	2026-08-18 16:27:47.825149+05:30	2026-08-18 16:27:47.825149+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.8646	severe	0	152	616	415	null	0.243797	8ad55e28-3dcb-4044-a574-d2b645eac76d	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.7152	severe	522	375	297	265	null	0.075059	8d06f780-0de9-49e2-9b1c-8c9d7139573e	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.3973	minor	184	808	19	15	null	0.000272	aca3e57e-49f8-473c-8484-148f33ca26c8	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.2807	minor	765	434	28	25	null	0.000668	688c75d4-855c-4324-9e08-6a57ed22c7a2	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	5dced117-c5b2-4be6-91fb-a076a6ce0d21	0.2681	minor	240	797	28	29	null	0.000774	d5852173-054d-4c8e-8d24-d7bcd02f1a4e	2026-08-18 18:20:29.881764+05:30	2026-08-18 18:20:29.881764+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	75bb6f49-597f-4630-bfe1-6b436744a217	a41cd314-1427-4003-a2b9-313216c56fd7	0.4722	severe	164	77	705	354	null	0.215101	3a402584-adf8-42b7-971f-8c9db074efb1	2026-08-18 19:12:39.283719+05:30	2026-08-18 19:12:39.283719+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	049e1d42-6d2d-452f-9147-43ab3a616694	9be73f34-ff6f-41bb-aaf4-c81d8abfb90b	0.6132	minor	285	81	18	36	null	0.003246	4f408d67-061f-4415-9aec-538b8e90ae5f	2026-08-18 19:12:43.056949+05:30	2026-08-18 19:12:43.056949+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	049e1d42-6d2d-452f-9147-43ab3a616694	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.4787	severe	34	248	268	98	null	0.131547	114f0a59-61f4-4ccf-b1a0-5ed19631a770	2026-08-18 19:12:43.056949+05:30	2026-08-18 19:12:43.056949+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	e08d1eb7-ba4d-4a0a-b173-3e4b0d4f7d2b	802cacb5-e296-4b62-8f5f-4fcbd34a6503	0.3884	moderate	251	337	199	91	null	0.059092	df1c69bb-4383-4121-a77b-402d2c7f4b04	2026-08-18 19:12:46.282382+05:30	2026-08-18 19:12:46.282382+05:30
\.


--
-- Data for Name: inspection_images; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inspection_images (inspection_id, cloudinary_public_id, secure_url, thumbnail_url, view_angle, width, height, file_size_bytes, format, sequence_no, status, failure_reason, quality_report, id, created_at, updated_at) FROM stdin;
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qzpsklymqo3cvzhbjf96	https://res.cloudinary.com/utlka8ks/image/upload/v1787037277/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qzpsklymqo3cvzhbjf96.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787037277/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qzpsklymqo3cvzhbjf96.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	b3c1425e-776f-40a7-81bc-ed57a2e56734	2026-08-18 12:44:40.034595+05:30	2026-08-18 12:44:59.964679+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/cvc8bwj96izzsshbukhf	https://res.cloudinary.com/utlka8ks/image/upload/v1787037278/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/cvc8bwj96izzsshbukhf.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787037278/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/cvc8bwj96izzsshbukhf.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	76aae949-89b9-4565-a491-c9ec44fb0923	2026-08-18 12:44:40.034595+05:30	2026-08-18 12:45:03.833966+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/rovrdv4vsdmjbauuzkug	https://res.cloudinary.com/utlka8ks/image/upload/v1787037279/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/rovrdv4vsdmjbauuzkug.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787037279/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/rovrdv4vsdmjbauuzkug.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	ac175af4-e8f5-453e-a5cc-ee0d0c49e7f6	2026-08-18 12:44:40.034595+05:30	2026-08-18 12:45:07.277655+05:30
b9ddc102-aa6c-40bb-9cca-71dab429b2ab	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/urduusld8qhi0inowqgf	https://res.cloudinary.com/utlka8ks/image/upload/v1787037279/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/urduusld8qhi0inowqgf.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787037279/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/urduusld8qhi0inowqgf.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	831c1497-13f3-4a93-818a-a1c50469cb97	2026-08-18 12:44:40.034595+05:30	2026-08-18 12:45:10.509828+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qt6ehx5ghgz1pmmypu4k	https://res.cloudinary.com/utlka8ks/image/upload/v1787039945/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qt6ehx5ghgz1pmmypu4k.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787039945/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/qt6ehx5ghgz1pmmypu4k.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	dadaa205-d762-4b55-883f-dce322cb3299	2026-08-18 13:29:08.042434+05:30	2026-08-18 13:29:10.94124+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/y3xmdk7zl4ooypcmggid	https://res.cloudinary.com/utlka8ks/image/upload/v1787039946/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/y3xmdk7zl4ooypcmggid.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787039946/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/y3xmdk7zl4ooypcmggid.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	0e40a25a-0cd4-47ba-b5ca-51dbcd7d27cb	2026-08-18 13:29:08.042434+05:30	2026-08-18 13:29:13.868479+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/fnuvylbxctkkq4xuhdec	https://res.cloudinary.com/utlka8ks/image/upload/v1787039947/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/fnuvylbxctkkq4xuhdec.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787039947/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/fnuvylbxctkkq4xuhdec.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	209d7f94-3f02-4cbe-9179-f08b8f32821c	2026-08-18 13:29:08.042434+05:30	2026-08-18 13:29:16.759006+05:30
cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/r3nr5cu5qqicfjn6o3xm	https://res.cloudinary.com/utlka8ks/image/upload/v1787039947/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/r3nr5cu5qqicfjn6o3xm.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787039947/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/r3nr5cu5qqicfjn6o3xm.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	32152275-4ba8-4a3d-9f54-9abd4c09a271	2026-08-18 13:29:08.042434+05:30	2026-08-18 13:29:19.702735+05:30
074094a4-77af-408c-ab06-6eda073d3df8	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/isntx6autnigi3dygaxf	https://res.cloudinary.com/utlka8ks/image/upload/v1787040090/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/isntx6autnigi3dygaxf.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040090/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/isntx6autnigi3dygaxf.jpg	\N	1300	893	189916	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	b6b8ee05-8838-4f76-a97c-655f47d0d151	2026-08-18 13:31:30.587732+05:30	2026-08-18 13:31:33.940245+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/gbhi5zu4hpqso9749cdv	https://res.cloudinary.com/utlka8ks/image/upload/v1787040140/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/gbhi5zu4hpqso9749cdv.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040140/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/gbhi5zu4hpqso9749cdv.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	47001255-28ba-43c1-aebf-072b6817411a	2026-08-18 13:32:22.602789+05:30	2026-08-18 13:32:25.251256+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/ax9twaufsg0gchvgcd6q	https://res.cloudinary.com/utlka8ks/image/upload/v1787040141/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/ax9twaufsg0gchvgcd6q.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040141/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/ax9twaufsg0gchvgcd6q.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	55019291-31ab-4d88-be1a-a97d94698b36	2026-08-18 13:32:22.602789+05:30	2026-08-18 13:32:28.564658+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/mth0yka32klylmv2lfca	https://res.cloudinary.com/utlka8ks/image/upload/v1787040141/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/mth0yka32klylmv2lfca.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040141/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/mth0yka32klylmv2lfca.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	610f294b-4b90-499a-8b32-93ddabe4ed6b	2026-08-18 13:32:22.602789+05:30	2026-08-18 13:32:32.456464+05:30
cd669392-b28f-4dd0-a260-6a10d074c28b	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/dkeho1ntft7yp6hmsag7	https://res.cloudinary.com/utlka8ks/image/upload/v1787040142/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/dkeho1ntft7yp6hmsag7.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787040142/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/dkeho1ntft7yp6hmsag7.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	56b9c8b4-bda2-4763-b70f-58cf376cbd75	2026-08-18 13:32:22.602789+05:30	2026-08-18 13:32:35.841038+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/x23kfm4awlrv8qzw9kvy	https://res.cloudinary.com/utlka8ks/image/upload/v1787050357/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/x23kfm4awlrv8qzw9kvy.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050357/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/x23kfm4awlrv8qzw9kvy.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	37bb03ec-5aa6-4fdd-8a9b-68d21fa4f1a8	2026-08-18 16:22:41.31026+05:30	2026-08-18 16:22:49.844106+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/oha78puvpmzdqp7pchxg	https://res.cloudinary.com/utlka8ks/image/upload/v1787050359/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/oha78puvpmzdqp7pchxg.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050359/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/oha78puvpmzdqp7pchxg.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	a3e066b5-8aba-4e2d-be33-485ca76e361f	2026-08-18 16:22:41.31026+05:30	2026-08-18 16:22:53.559987+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/e8ecxgsh51ux14itiypl	https://res.cloudinary.com/utlka8ks/image/upload/v1787050360/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/e8ecxgsh51ux14itiypl.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050360/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/e8ecxgsh51ux14itiypl.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	d41fc5b7-4b31-4220-91a8-abd94c433865	2026-08-18 16:22:41.31026+05:30	2026-08-18 16:22:57.974871+05:30
514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/kpdqzx0wxlpdjc2bhyuj	https://res.cloudinary.com/utlka8ks/image/upload/v1787050361/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/kpdqzx0wxlpdjc2bhyuj.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050361/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/kpdqzx0wxlpdjc2bhyuj.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	4974153c-05e9-4171-84f2-6f950b163d22	2026-08-18 16:22:41.31026+05:30	2026-08-18 16:23:01.423813+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/vp9iimnkkgromqa9ns79	https://res.cloudinary.com/utlka8ks/image/upload/v1787050659/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/vp9iimnkkgromqa9ns79.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050659/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/vp9iimnkkgromqa9ns79.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	0020b111-0adb-4e04-a807-b4fbe7226233	2026-08-18 16:27:41.416937+05:30	2026-08-18 16:27:44.363519+05:30
7a36f7ea-a229-4f10-9005-49673489c5f5	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/wzbu1w8mrxaep3duvglv	https://res.cloudinary.com/utlka8ks/image/upload/v1787050661/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/wzbu1w8mrxaep3duvglv.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787050661/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/wzbu1w8mrxaep3duvglv.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	db644740-6b72-4998-adaa-52d04816f7f2	2026-08-18 16:27:41.416937+05:30	2026-08-18 16:27:47.823149+05:30
08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/yhbkyyhcue5reg7etuwq	https://res.cloudinary.com/utlka8ks/image/upload/v1787057420/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/yhbkyyhcue5reg7etuwq.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787057420/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/yhbkyyhcue5reg7etuwq.jpg	\N	1024	1024	128400	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 974.56, "brightness": 85.6}	29871565-7570-4a1f-9fdc-1cd0c4e9b3e7	2026-08-18 18:20:20.483339+05:30	2026-08-18 18:20:29.879764+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/uetmk0fhwhtubun2qgkc	https://res.cloudinary.com/utlka8ks/image/upload/v1787060549/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/uetmk0fhwhtubun2qgkc.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787060549/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/uetmk0fhwhtubun2qgkc.jpg	\N	782	392	24942	jpg	0	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 203.31, "brightness": 103.5}	f5a9d4ae-6401-4e57-8073-ab989174c63c	2026-08-18 19:12:32.165328+05:30	2026-08-18 19:12:35.153871+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/htkmy5rve8hykaypelrm	https://res.cloudinary.com/utlka8ks/image/upload/v1787060550/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/htkmy5rve8hykaypelrm.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787060550/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/htkmy5rve8hykaypelrm.jpg	\N	1300	893	189916	jpg	1	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 913.65, "brightness": 103.27}	75bb6f49-597f-4630-bfe1-6b436744a217	2026-08-18 19:12:32.165328+05:30	2026-08-18 19:12:39.281717+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/lhfmafjdu0emhe3fqtor	https://res.cloudinary.com/utlka8ks/image/upload/v1787060551/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/lhfmafjdu0emhe3fqtor.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787060551/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/lhfmafjdu0emhe3fqtor.jpg	\N	547	365	19991	jpg	2	processed	\N	{"warnings": [], "is_blurry": false, "blur_score": 354.59, "brightness": 130.25}	049e1d42-6d2d-452f-9147-43ab3a616694	2026-08-18 19:12:32.165328+05:30	2026-08-18 19:12:43.055949+05:30
8cb902b4-f113-4d88-a3d1-28646407bcb7	dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/xcdkm1zwmgbb925c8hmf	https://res.cloudinary.com/utlka8ks/image/upload/v1787060552/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/xcdkm1zwmgbb925c8hmf.jpg	https://res.cloudinary.com/utlka8ks/image/upload/c_fill,w_320,h_320,q_auto/v1787060552/dent-inspections/1159bb7c-34c8-44b1-a542-9aa1c7512f55/xcdkm1zwmgbb925c8hmf.jpg	\N	678	452	14717	jpg	3	processed	\N	{"warnings": ["Image appears blurry or out of focus. Damage edges may be missed."], "is_blurry": true, "blur_score": 70.25, "brightness": 114.59}	e08d1eb7-ba4d-4a0a-b173-3e4b0d4f7d2b	2026-08-18 19:12:32.165328+05:30	2026-08-18 19:12:46.281382+05:30
\.


--
-- Data for Name: inspections; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inspections (user_id, reference_code, status, overall_severity, damage_score, total_detections, total_area_percent, damage_summary, model_name, model_version, processing_completed_at, processing_ms, error_code, error_message, idempotency_key, id, created_at, updated_at, deleted_at, detection_preset, detection_settings, below_threshold_count, model_backend, customer_name, vehicle_type) FROM stdin;
1159bb7c-34c8-44b1-a542-9aa1c7512f55	INS-20260818-653687	completed	severe	89	3	39.81	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 58.11}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 16:27:47.845699+05:30	6403	\N	\N	ui-26019eb6-e9aa-4044-bee2-1e9d32a7696b	7a36f7ea-a229-4f10-9005-49673489c5f5	2026-08-18 16:27:41.414939+05:30	2026-08-18 16:27:47.846699+05:30	\N	sensitive	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.22, "input_size": 1024}	1	ultralytics	\N	\N
1159bb7c-34c8-44b1-a542-9aa1c7512f55	INS-20260818-4E58B2	completed	severe	97	4	10.22	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 19.06}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 19:12:46.308379+05:30	14117	\N	\N	ui-4095e1b5-d43c-4155-8363-5a019e8462bf	8cb902b4-f113-4d88-a3d1-28646407bcb7	2026-08-18 19:12:32.148327+05:30	2026-08-18 19:12:46.309379+05:30	\N	balanced	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.35, "input_size": 1024}	4	ultralytics	\N	\N
1159bb7c-34c8-44b1-a542-9aa1c7512f55	INS-20260818-E00A8E	completed	severe	100	5	22.27	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 3, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 67.23}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 12:45:10.536881+05:30	30451	\N	\N	ui-74c4bfb4-bf35-436d-b333-cfbe8046f257	b9ddc102-aa6c-40bb-9cca-71dab429b2ab	2026-08-18 12:44:40.029596+05:30	2026-08-18 12:45:10.53788+05:30	\N	\N	\N	0	ultralytics	\N	\N
1159bb7c-34c8-44b1-a542-9aa1c7512f55	INS-20260818-B48066	completed	severe	81	2	49.78	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 28.27}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 13:31:33.959246+05:30	3341	\N	\N	ui-9c542ef4-3011-4de1-b644-0561937237d9	074094a4-77af-408c-ab06-6eda073d3df8	2026-08-18 13:31:30.584735+05:30	2026-08-18 13:31:33.960247+05:30	\N	sensitive	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.22, "input_size": 1024}	0	ultralytics	\N	\N
1159bb7c-34c8-44b1-a542-9aa1c7512f55	INS-20260818-B08575	completed	severe	80	5	32.06	[{"count": 5, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": "severe", "total_area_percent": 32.06}, {"count": 0, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 18:20:29.912804+05:30	9383	\N	\N	ui-ec67e7a3-6dc3-4428-979a-45d8089dc547	08ed5c80-fa5b-4b1e-84e0-b41becbfb5d8	2026-08-18 18:20:20.477337+05:30	2026-08-18 18:20:29.913853+05:30	\N	sensitive	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.22, "input_size": 1024}	2	ultralytics	\N	\N
1159bb7c-34c8-44b1-a542-9aa1c7512f55	INS-20260818-4FBDDE	completed	severe	97	4	10.22	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 2, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 19.06}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 16:23:01.451816+05:30	20080	\N	\N	ui-1d72d076-0566-4124-a0fc-130a36eaab6d	514b1f54-1e80-4bf8-aa4b-cd4dd6783a4a	2026-08-18 16:22:41.293252+05:30	2026-08-18 16:23:01.452814+05:30	\N	balanced	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.35, "input_size": 1024}	4	ultralytics	\N	\N
1159bb7c-34c8-44b1-a542-9aa1c7512f55	INS-20260818-3F1E1F	completed	severe	100	7	25.08	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 5, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": "severe", "total_area_percent": 78.5}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 1, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": "severe", "total_area_percent": 21.51}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 13:29:19.725737+05:30	11662	\N	\N	ui-4d4802ba-e586-435c-88e6-101d0a8a9031	cd3dfb1b-a88e-4a5e-b6df-959f1bba46f5	2026-08-18 13:29:08.040434+05:30	2026-08-18 13:29:19.726739+05:30	\N	sensitive	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.22, "input_size": 1024}	1	ultralytics	\N	\N
1159bb7c-34c8-44b1-a542-9aa1c7512f55	INS-20260818-23E9EA	completed	minor	8	1	0.08	[{"count": 0, "label": "Dent", "class_key": "dent", "color_hex": "#38bdf8", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Scratch", "class_key": "scratch", "color_hex": "#f59e0b", "is_critical": false, "max_severity": null, "total_area_percent": 0.0}, {"count": 1, "label": "Crack", "class_key": "crack", "color_hex": "#f43f5e", "is_critical": false, "max_severity": "minor", "total_area_percent": 0.32}, {"count": 0, "label": "Glass Shatter", "class_key": "glass_shatter", "color_hex": "#c084fc", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Lamp Broken", "class_key": "lamp_broken", "color_hex": "#fde047", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}, {"count": 0, "label": "Tire Flat", "class_key": "tire_flat", "color_hex": "#34d399", "is_critical": true, "max_severity": null, "total_area_percent": 0.0}]	autodent-yolo11m	1.0.0	2026-08-18 13:32:35.868041+05:30	13245	\N	\N	ui-07e6f93b-cc63-43bb-80f0-01384246949f	cd669392-b28f-4dd0-a260-6a10d074c28b	2026-08-18 13:32:22.600791+05:30	2026-08-18 13:32:35.869041+05:30	\N	strict	{"iou": 0.45, "augment": false, "use_clahe": false, "confidence": 0.5, "input_size": 1024}	7	ultralytics	\N	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (email, password_hash, full_name, phone, role, is_active, id, created_at, updated_at, deleted_at) FROM stdin;
test@yopmail.com	scrypt:32768:8:1$lmFAyTGklbhrHsq0$f4f8f7ae67f305df287ebeaa8cfa9c2b7fa00c4337846633349c39db88dbb2bcb8f09c2b87c86dfe639348482ca91e8e333d75bfc801be179968689352ae7b5d	Test	\N	user	t	1159bb7c-34c8-44b1-a542-9aa1c7512f55	2026-08-18 12:41:59.924247+05:30	2026-08-18 12:41:59.924247+05:30	\N
\.


--
-- Name: damage_types damage_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.damage_types
    ADD CONSTRAINT damage_types_pkey PRIMARY KEY (id);


--
-- Name: detections detections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detections
    ADD CONSTRAINT detections_pkey PRIMARY KEY (id);


--
-- Name: inspection_images inspection_images_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inspection_images
    ADD CONSTRAINT inspection_images_pkey PRIMARY KEY (id);


--
-- Name: inspections inspections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inspections
    ADD CONSTRAINT inspections_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_damage_types_class_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_damage_types_class_key ON public.damage_types USING btree (class_key);


--
-- Name: ix_detections_damage_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_detections_damage_type_id ON public.detections USING btree (damage_type_id);


--
-- Name: ix_detections_inspection_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_detections_inspection_id ON public.detections USING btree (inspection_id);


--
-- Name: ix_detections_inspection_image_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_detections_inspection_image_id ON public.detections USING btree (inspection_image_id);


--
-- Name: ix_inspection_images_inspection_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspection_images_inspection_id ON public.inspection_images USING btree (inspection_id);


--
-- Name: ix_inspections_customer_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_customer_name ON public.inspections USING btree (customer_name);


--
-- Name: ix_inspections_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_deleted_at ON public.inspections USING btree (deleted_at);


--
-- Name: ix_inspections_idempotency_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_inspections_idempotency_key ON public.inspections USING btree (idempotency_key);


--
-- Name: ix_inspections_reference_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_inspections_reference_code ON public.inspections USING btree (reference_code);


--
-- Name: ix_inspections_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_status ON public.inspections USING btree (status);


--
-- Name: ix_inspections_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_user_created ON public.inspections USING btree (user_id, created_at);


--
-- Name: ix_inspections_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_user_id ON public.inspections USING btree (user_id);


--
-- Name: ix_inspections_vehicle_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inspections_vehicle_type ON public.inspections USING btree (vehicle_type);


--
-- Name: ix_users_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_deleted_at ON public.users USING btree (deleted_at);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: detections detections_damage_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detections
    ADD CONSTRAINT detections_damage_type_id_fkey FOREIGN KEY (damage_type_id) REFERENCES public.damage_types(id) ON DELETE RESTRICT;


--
-- Name: detections detections_inspection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detections
    ADD CONSTRAINT detections_inspection_id_fkey FOREIGN KEY (inspection_id) REFERENCES public.inspections(id) ON DELETE CASCADE;


--
-- Name: detections detections_inspection_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detections
    ADD CONSTRAINT detections_inspection_image_id_fkey FOREIGN KEY (inspection_image_id) REFERENCES public.inspection_images(id) ON DELETE CASCADE;


--
-- Name: inspection_images inspection_images_inspection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inspection_images
    ADD CONSTRAINT inspection_images_inspection_id_fkey FOREIGN KEY (inspection_id) REFERENCES public.inspections(id) ON DELETE CASCADE;


--
-- Name: inspections inspections_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inspections
    ADD CONSTRAINT inspections_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

