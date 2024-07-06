-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 06-07-2024 a las 18:34:01
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `tierra-de-paz`
--

--
-- Volcado de datos para la tabla `usuario`
--

INSERT INTO `usuario` (`id`, `nombre`, `correo`, `contraseña`, `foto_perfil`, `rol`) VALUES
(13, 'administrador', 'administrador@tierradepaz.org', '$2b$12$ajJdKj5kiip/tdttEXij0.nrxJfmrbBynZkzD/UMI7gTxAqVS9L/K', NULL, 1),
(14, 'coordinador', 'coordinador@tierradepaz.org', '$2b$12$tk4YmKNB0E/8HKrx7YozqOSE1yD/4tqvIEnnhsaBX9Rai5jhPltNy', NULL, 2),
(16, 'Monitor', 'monitor@tierradepaz.org', '$2b$12$BDZJMZXNgD1/zmeWNSaEOeHfNQLzmWScKC7Vx88U09AHHoFZVi4dm', NULL, 3);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
