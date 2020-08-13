import React, { Component } from "react";
import { Link } from "react-router-dom";

import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";

class CaseCounts extends Component {
    render() {
        return (
          <Row>
            <Col xs="12"><p>This page will show case counts</p></Col>
            <Col xs="12"><p>To go back, click <Link to="/">here</Link></p>.</Col>
          </Row>
        );
      }
}
export default CaseCounts;