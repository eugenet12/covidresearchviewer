import React, { Component } from "react";
import Card from "react-bootstrap/Card";
import CardDeck from "react-bootstrap/CardDeck";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import FormControl from "react-bootstrap/FormControl";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import Row from "react-bootstrap/Row";
import { Route, Switch, withRouter } from "react-router-dom";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSearch } from "@fortawesome/free-solid-svg-icons";

import { Research, SearchResults, TreatmentView } from "./_research.js";
import { AboutModal } from "./_about.js";
import "./App.css";

String.prototype.capitalize = function () {
  return this.charAt(0).toUpperCase() + this.slice(1);
};

class Header extends Component {
  constructor(props) {
    super(props);
    this.handleSearchChange = this.handleSearchChange.bind(this);
    this.handleSearchKeyDown = this.handleSearchKeyDown.bind(this);
    this.isTopicSelected = this.isTopicSelected.bind(this);
    this.renderTopicSelector = this.renderTopicSelector.bind(this);
    this.searchPapers = this.searchPapers.bind(this);
    if (this.props.topic === "search") {
      this.state = {
        searchQuery: this.props.subtopic,
      };
    } else {
      this.state = {
        searchQuery: "",
      };
    }
  }

  handleSearchChange(e) {
    this.setState({ searchQuery: e.target.value });
  }

  handleSearchKeyDown(e) {
    // search on enter
    if (e.key === "Enter") {
      this.searchPapers();
    }
  }

  isTopicSelected(topic) {
    return this.props.topic === topic;
  }

  renderTopicSelector(topic) {
    let href = "/" + topic;
    return (
      <Nav.Link
        href={href}
        key={topic}
        className={this.isTopicSelected(topic) ? "selectedPage" : ""}
      >
        {topic.capitalize()}
      </Nav.Link>
    );
  }

  searchPapers(e) {
    e.preventDefault(); // prevent default form submission
    window.open(
      "/search/" + encodeURIComponent(this.state.searchQuery),
      "_self"
    );
  }

  render() {
    let topics = [
      "treatment",
      "vaccine",
      "prevention",
      "diagnosis",
      "transmission",
      "epidemiology",
      "latest",
    ];
    let topicElements = topics.map(this.renderTopicSelector);
    return (
      <div>
        <Navbar className="header">
          <Navbar.Brand href="/">
            <img
              src="/bacteria-infection-virus.svg"
              width="30"
              height="30"
              className="d-inline-block align-top"
              alt="Virus Logo"
            />{" "}
            Covid-19 Research Portal
          </Navbar.Brand>
        </Navbar>
        <Navbar className="subHeader">
          <Nav className="mr-auto justify-content-center">{topicElements}</Nav>
          <SearchBar topic={this.props.topic} subtopic={this.props.subtopic} />
        </Navbar>
      </div>
    );
  }
}

class SearchBar extends Component {
  constructor(props) {
    super(props);
    this.handleSearchChange = this.handleSearchChange.bind(this);
    this.handleSearchKeyDown = this.handleSearchKeyDown.bind(this);
    this.searchPapers = this.searchPapers.bind(this);
    if (this.props.topic === "search") {
      this.state = {
        searchQuery: this.props.subtopic,
      };
    } else {
      this.state = {
        searchQuery: "",
      };
    }
  }

  handleSearchChange(e) {
    this.setState({ searchQuery: e.target.value });
  }

  handleSearchKeyDown(e) {
    // search on enter
    if (e.key === "Enter") {
      this.searchPapers();
    }
  }

  searchPapers(e) {
    e.preventDefault(); // prevent default form submission
    if (this.state.searchQuery.length > 0) {
      window.open(
        "/search/" + encodeURIComponent(this.state.searchQuery),
        "_self"
      );
    }
  }

  render() {
    // landing page
    if (this.props.topic.length === 0) {
      return (
        <Form inline onSubmit={this.searchPapers}>
          <Form.Control
            type="text"
            placeholder="Search Papers"
            onChange={this.handleSearchChange}
            value={this.state.searchQuery}
            id="landing-page-search-bar"
            className="rounded-pill-left border-right-0"
          />
          <Button
            onClick={this.searchPapers}
            id="landing-page-button"
            className="rounded-pill-right border-left-0"
          >
            <FontAwesomeIcon icon={faSearch} />
          </Button>
        </Form>
      );
      // main page
    } else {
      return (
        <Form inline onSubmit={this.searchPapers}>
          <FormControl
            type="text"
            placeholder="Search Papers"
            className="mr-sm-2"
            onChange={this.handleSearchChange}
            value={decodeURIComponent(this.state.searchQuery)}
          />
          <Button variant="outline-light" onClick={this.searchPapers}>
            <FontAwesomeIcon icon={faSearch} />
          </Button>
        </Form>
      );
    }
  }
}

// first splash page
class LandingPage extends Component {
  state = {
    showAboutModal: false,
  };

  constructor(props) {
    super(props);
    this.hideAboutModal = this.hideAboutModal.bind(this);
    this.showAboutModal = this.showAboutModal.bind(this);
  }

  hideAboutModal() {
    this.setState({ showAboutModal: false });
  }

  showAboutModal(e) {
    e.stopPropagation();
    this.setState({ showAboutModal: true });
  }

  render() {
    return (
      <Container fluid className="h-100 landingContainer">
        <Row className="h-100">
          <Col xs="12" className="my-auto text-center">
            <img
              src="bacteria-infection-virus_inverted.png"
              alt="Virus logo"
              height="100"
              width="100"
            />
            <h1>Covid-19 Research Portal</h1>
            <br />
            <Col sm={{ span: 6, offset: 3 }}>
              <SearchBar topic={""} subtopic={""} />
            </Col>
            <br />
            <br />
            <CardDeck className="frontPageDeck">
              <Card>
                <Card.Body>
                  <img
                    src="/treatment.png"
                    width="80"
                    height="80"
                    className="Ed-inline-block align-top"
                    alt="Treatment"
                  />
                  <Card.Title>Treatment</Card.Title>
                  <Card.Text>
                    Find research papers on potential COVID-19 treatments.
                  </Card.Text>
                </Card.Body>
                <Card.Footer className="bg-transparent">
                  <Card.Link href="/treatment">View Summary</Card.Link>
                </Card.Footer>
              </Card>
              <Card>
                <Card.Body>
                  <img
                    src="/vaccine.png"
                    width="80"
                    height="80"
                    className="Ed-inline-block align-top"
                    alt="Vaccine"
                  />
                  <Card.Title>Vaccine</Card.Title>
                  <Card.Text>
                    Find research papers on finding a vaccine for COVID-19.
                  </Card.Text>
                </Card.Body>
                <Card.Footer className="bg-transparent">
                  <Card.Link href="/vaccine">View Summary</Card.Link>
                </Card.Footer>
              </Card>
              <Card>
                <Card.Body>
                  <img
                    src="/prevention.png"
                    width="80"
                    height="80"
                    className="Ed-inline-block align-top"
                    alt="Prevention"
                  />
                  <Card.Title>Prevention</Card.Title>
                  <Card.Text>
                    Find research papers on how COVID-19 can be prevented.
                  </Card.Text>
                </Card.Body>
                <Card.Footer className="bg-transparent">
                  <Card.Link href="/prevention">View Summary</Card.Link>
                </Card.Footer>
              </Card>
              <Card>
                <Card.Body>
                  <img
                    src="/diagnosis.png"
                    width="80"
                    height="80"
                    className="Ed-inline-block align-top"
                    alt="Diagnosis"
                  />
                  <Card.Title>Diagnosis</Card.Title>
                  <Card.Text>
                    Find research papers on testing for and diagnosing COVID-19.
                  </Card.Text>
                </Card.Body>
                <Card.Footer className="bg-transparent">
                  <Card.Link href="/diagnosis">View Summary</Card.Link>
                </Card.Footer>
              </Card>
            </CardDeck>
            <CardDeck className="frontPageDeck">
              <Card>
                <Card.Body>
                  <img
                    src="/transmission.png"
                    width="80"
                    height="80"
                    className="Ed-inline-block align-top"
                    alt="Transmission"
                  />
                  <Card.Title>Transmission</Card.Title>
                  <Card.Text>
                    Find research papers on how COVID-19 is transmitted.
                  </Card.Text>
                </Card.Body>
                <Card.Footer className="bg-transparent">
                  <Card.Link href="/transmission">View Summary</Card.Link>
                </Card.Footer>
              </Card>
              <Card>
                <Card.Body>
                  <img
                    src="/epidemiology.png"
                    width="80"
                    height="80"
                    className="Ed-inline-block align-top"
                    alt="Epidemiology"
                  />
                  <Card.Title>Epidemiology</Card.Title>
                  <Card.Text>
                    Find research papers on measuring the spread of COVID-19.
                  </Card.Text>
                </Card.Body>
                <Card.Footer className="bg-transparent">
                  <Card.Link href="/epidemiology">View Summary</Card.Link>
                </Card.Footer>
              </Card>
              <Card>
                <Card.Body>
                  <img
                    src="/trendingpaper.png"
                    width="80"
                    height="80"
                    className="Ed-inline-block align-top"
                    alt="Latest Papers"
                  />
                  <Card.Title>Latest Papers</Card.Title>
                  <Card.Text>
                    Find the latest papers discussing COVID-19.
                  </Card.Text>
                </Card.Body>
                <Card.Footer className="bg-transparent">
                  <Card.Link href="/latest">View Summary</Card.Link>
                </Card.Footer>
              </Card>
              <Card>
                <Card.Body>
                  <img
                    src="/aboutus.png"
                    width="80"
                    height="80"
                    className="Ed-inline-block align-top"
                    alt="About Us"
                  />
                  <Card.Title>About</Card.Title>
                  <Card.Text>
                    Learn more the product and how it was made.
                  </Card.Text>
                </Card.Body>
                <Card.Footer className="bg-transparent">
                  <Card.Link href="#" onClick={this.showAboutModal}>
                    About
                  </Card.Link>
                </Card.Footer>
              </Card>{" "}
            </CardDeck>
          </Col>
          <AboutModal
            show={this.state.showAboutModal}
            handleClose={this.hideAboutModal}
          />
        </Row>
      </Container>
    );
  }
}

// remainder of content is served through here
class MainPage extends Component {
  render() {
    let validTopics = new Set([
      "treatment",
      "vaccine",
      "prevention",
      "diagnosis",
      "transmission",
      "epidemiology",
      "latest",
      "search",
    ]);
    if (!validTopics.has(this.props.topic)) {
      return (
        <Container fluid>
          <Header topic={this.props.topic} subtopic={this.props.subtopic} />
          <p style={{ marginTop: "15px", marginLeft: "15px" }}>
            Page not found! Please click one of the links in the header above to
            continue.
          </p>
        </Container>
      );
    }
    return (
      <Container fluid>
        <Header topic={this.props.topic} subtopic={this.props.subtopic} />
        <Switch>
          <Route
            path="/search/:query"
            render={(props) => (
              <SearchResults
                topic={this.props.topic}
                query={this.props.subtopic}
                filters={this.props.filters}
                {...props}
              />
            )}
          />
          <Route
            path="/treatment"
            render={(props) => (
              <TreatmentView
                topic={this.props.topic}
                subtopic={this.props.subtopic}
                filters={this.props.filters}
                {...props}
              />
            )}
          />
          <Route
            path="/"
            render={(props) => (
              <Research
                topic={this.props.topic}
                subtopic={this.props.subtopic}
                filters={this.props.filters}
                {...props}
              />
            )}
          />
        </Switch>
      </Container>
    );
  }
}

class App extends Component {
  constructor(props) {
    super(props);
    this.getTopicAndSubtopic = this.getTopicAndSubtopic.bind(this);
  }
  // get the topic and subtopic based on the url
  getTopicAndSubtopic() {
    let tokens = this.props.location.search.split("?filters=");
    console.log(tokens)
    let filters;
    if (tokens.length <= 1 || tokens[1] === "") {
      filters = [];
    } else {
      filters = tokens[1].split(",");
    }
    tokens = this.props.location.pathname.split("/");
    if (tokens.length <= 1 || tokens[1] === "") {
      return ["latest", "", filters];
    } else if (tokens.length === 2) {
      return [tokens[1], "", filters];
    } else {
      return [tokens[1], tokens[2], filters];
    }
  }
  render() {
    let urlParse = this.getTopicAndSubtopic();
    let topic = urlParse[0];
    let subtopic = urlParse[1];
    let filters = urlParse[2];
    console.log(topic, subtopic, filters);
    return (
      <Switch>
        <Route exact path="/" component={LandingPage} />
        <Route
          path="/"
          render={(props) => (
            <MainPage topic={topic} subtopic={subtopic} filters={filters} {...props} />
          )}
        />
      </Switch>
    );
  }
}

export default withRouter((props) => <App {...props} />);
